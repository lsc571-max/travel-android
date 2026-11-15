package kr.pureun.travel;

import com.k2fsa.sherpa.onnx.OfflineModelConfig;
import com.k2fsa.sherpa.onnx.OfflineRecognizer;
import com.k2fsa.sherpa.onnx.OfflineRecognizerConfig;
import com.k2fsa.sherpa.onnx.OfflineRecognizerResult;
import com.k2fsa.sherpa.onnx.OfflineSenseVoiceModelConfig;
import com.k2fsa.sherpa.onnx.OfflineStream;
import com.k2fsa.sherpa.onnx.OfflineWhisperModelConfig;
import com.k2fsa.sherpa.onnx.SileroVadModelConfig;
import com.k2fsa.sherpa.onnx.SpeechSegment;
import com.k2fsa.sherpa.onnx.Vad;
import com.k2fsa.sherpa.onnx.VadModelConfig;

import java.util.Arrays;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 폰 안 음성 인식의 핵심 (안드로이드 기능을 쓰지 않는 순수 자바 → PC에서도 시험 가능).
 * 16kHz 소리를 계속 받아서, 말소리 구간을 찾아(VAD) 문장 단위로 글자로 바꾼다(Whisper / SenseVoice).
 * 말하는 사람의 목소리 크기·높낮이도 함께 잰다.
 */
class SttCore {
    interface Listener {
        void onPartial(String text);
        /** db: 평균 크기(dBFS), hz: 목소리 높낮이(0 = 모름), seconds: 말한 길이,
         *  at: 저장한 소리에서의 자리 {파일 시작 표본, 파일 끝 표본, 들린 시각 시작 ms, 끝 ms} (저장하지 않으면 null) */
        void onFinal(String text, String lang, float db, float hz, float seconds, long[] at);
    }

    static final int RATE = 16000;
    private static final int WINDOW = 512;

    private final String type;                 // "whisper" | "sensevoice"
    private final String[] files;              // whisper: encoder, decoder, tokens / sensevoice: model, tokens
    private final int threads;
    private final Vad vad;
    private final String vadModel;
    private final float minSilence;
    private volatile boolean noDecode = false;  // true = 말소리 구간만 찾고 받아 적지 않음 (Gemini가 저장된 소리를 직접 들을 때)
    private OfflineRecognizer rec;
    private String lang = "ko";
    private String recLang = "ko";              // 인식기에 실제로 걸려 있는 언어 (작업 스레드에서만 바꿈)
    private final Listener listener;
    private final ExecutorService worker = Executors.newSingleThreadExecutor(new java.util.concurrent.ThreadFactory() {
        @Override public Thread newThread(Runnable r) {
            Thread t = new Thread(r, "stt-work");
            try { t.setPriority(Thread.NORM_PRIORITY - 2); } catch (Throwable ignored) { }   // 받아 적기는 조금 낮은 우선순위로 (소리 재생이 먼저)
            return t;
        }
    });
    private final AtomicInteger pending = new AtomicInteger();
    private volatile int epoch = 0;

    // 말하는 중인 소리 (중간 글자용)
    private float[] cur = new float[RATE * 16];
    private int curLen = 0;
    private boolean speaking = false;
    private long lastPartialAt = 0;
    private volatile long partialCost = 0;      // 지난 중간 글자를 만드는 데 걸린 시간(ms)
    private volatile int seg = 0;               // 말소리 구간 번호 (구간이 바뀌면 지난 구간의 중간 글자는 버림)
    private final float[] pre = new float[RATE * 3 / 10];   // 말 시작 앞 0.3초
    private int prePos = 0;
    private float[] rest = new float[0];

    // 들은 소리 저장 (긴 무음만 빼고). fed = 마지막 reset 뒤 VAD에 넣은 표본 수, vadBase = 그때 저장소의 위치
    private AudioStore store;
    private long fed = 0, vadBase = 0;

    SttCore(String vadModel, String type, String[] files, int threads, float minSilence, Listener l) {
        this.type = type; this.files = files; this.threads = threads; this.listener = l;
        this.vadModel = vadModel; this.minSilence = minSilence;
        vad = newVad();
        rec = new OfflineRecognizer(config(lang));
    }

    private Vad newVad() {
        SileroVadModelConfig silero = SileroVadModelConfig.builder()
                .setModel(vadModel).setThreshold(0.5f)
                .setMinSilenceDuration(minSilence).setMinSpeechDuration(0.25f)
                .setWindowSize(WINDOW).setMaxSpeechDuration(25f).build();   // 쉬는 곳에서만 끊음 (쉬지 않고 25초를 넘길 때만 강제로 끊음)
        return new Vad(VadModelConfig.builder().setSileroVadModelConfig(silero)
                .setSampleRate(RATE).setNumThreads(1).setDebug(false).setProvider("cpu").build());
    }

    /** true = 받아 적지 않고 말소리 구간(저장된 자리)만 알려 줌. 글은 빈 문자열로 onFinal */
    void setNoDecode(boolean on) { noDecode = on; }

    interface TextCallback { void done(String text, String error); }

    /**
     * 저장해 둔 소리(16kHz)를 받아 적음: 말소리 구간으로 나눠(한 번에 25초까지) 차례로 받아 적고 이어 붙임.
     * 듣는 중의 받아 적기와 같은 줄에서 차례로 처리하므로 서로 섞이지 않음. language "" = 자동
     */
    void transcribe(final float[] samples, final String language, final TextCallback cb) {
        pending.incrementAndGet();
        worker.execute(new Runnable() {
            @Override public void run() {
                boolean turn = false;
                Vad v = null;
                final String old = recLang, want = language == null ? "" : language;
                try {
                    turn = Heavy.enter(180000);
                    if (!want.equals(old)) rec.setConfig(config(want));
                    v = newVad();
                    StringBuilder sb = new StringBuilder();
                    int off = 0;
                    while (samples.length - off >= WINDOW) {
                        v.acceptWaveform(Arrays.copyOfRange(samples, off, off + WINDOW));
                        off += WINDOW;
                        while (!v.empty()) { float[] s = v.front().getSamples(); v.pop(); appendText(sb, s); }
                    }
                    v.flush();
                    while (!v.empty()) { float[] s = v.front().getSamples(); v.pop(); appendText(sb, s); }
                    cb.done(sb.toString().trim(), null);
                } catch (Throwable t) {
                    cb.done("", String.valueOf(t.getMessage()));
                } finally {
                    try { if (!want.equals(old)) rec.setConfig(config(old)); } catch (Throwable ignored) { }
                    try { if (v != null) v.release(); } catch (Throwable ignored) { }
                    Heavy.done(turn);
                    pending.decrementAndGet();
                }
            }
        });
    }

    private void appendText(StringBuilder sb, float[] s) {
        if (s == null || s.length < RATE / 5 || rmsDb(s) < -55f) return;
        String t = decode(s)[0];
        if (!t.isEmpty()) { if (sb.length() > 0) sb.append(' '); sb.append(t); }
    }

    /** 엔진이 소리 끝에 붙이는 조용한 구간(1 = 0.01초). small 이하는 2초, turbo·large는 아래 padded()에서 직접 붙임 */
    private int tailPad() {
        String f = files.length > 0 ? files[0] : "";
        return big() ? Integer.getInteger("stt.tail", 50) : 200;
    }
    private boolean big() { String f = files.length > 0 ? files[0] : ""; return !(f.contains("small") || f.contains("base") || f.contains("tiny")); }
    /* turbo·large는 소리 뒤의 조용한 구간이 짧으면 같은 말을 되풀이해 적는 일이 있음.
       늘 길게 붙이면 느려지므로: 먼저 짧게(PAD1초) 붙여 받아 적고, 되풀이가 의심될 때만 길게(PAD2초) 붙여 한 번 더 받아 적음. 값은 시험으로 정함 */
    private static final float PAD1 = Float.parseFloat(System.getProperty("stt.pad1", "6")), PAD2 = Float.parseFloat(System.getProperty("stt.pad2", "10"));
    private float[] padded(float[] s, float sec) { return Arrays.copyOf(s, s.length + (int) (sec * RATE)); }
    /** 같은 말이 이어서 되풀이됐거나, 끝부분이 첫머리를 다시 적은 것처럼 보이는지 */
    static boolean suspicious(String text) {
        String n = text.replaceAll("[\\s.,!?。、，！？…~\\-]+", "").toLowerCase();
        if (n.length() < 4) return false;
        if (java.util.regex.Pattern.compile("(.{2,24})\\1").matcher(n).find()) return true;      // 바로 이어서 되풀이
        for (int k = Math.min(n.length() / 2, 30); k >= 3; k--) if (n.endsWith(n.substring(0, k))) return true; // 끝이 첫머리와 같음
        return false;
    }

    private OfflineRecognizerConfig config(String language) {
        OfflineModelConfig.Builder m = OfflineModelConfig.builder().setNumThreads(threads).setDebug(false).setProvider("cpu");
        if ("sensevoice".equals(type)) {
            m.setSenseVoice(OfflineSenseVoiceModelConfig.builder().setModel(files[0])
                    .setLanguage(language.isEmpty() ? "auto" : language).setInverseTextNormalization(true).build());
            m.setTokens(files[1]);
        } else {
            m.setWhisper(OfflineWhisperModelConfig.builder().setEncoder(files[0]).setDecoder(files[1])
                    .setLanguage(language).setTask("transcribe").setTailPaddings(tailPad()).build());
            m.setTokens(files[2]);
        }
        return OfflineRecognizerConfig.builder().setOfflineModelConfig(m.build()).setDecodingMethod("greedy_search").build();
    }

    /** 듣는 언어 바꾸기. ""이면 자동 감지 */
    synchronized void setLanguage(String language) {
        if (language == null) language = "";
        if (language.equals(lang)) return;
        lang = language;
        final String l = language;
        worker.execute(new Runnable() {
            @Override public void run() {
                try { rec.setConfig(config(l)); }
                catch (Throwable t) { try { rec.release(); } catch (Throwable ignored) { } rec = new OfflineRecognizer(config(l)); }
                recLang = l;
            }
        });
    }

    /** 들은 소리를 저장할 곳 (null = 저장 안 함) */
    synchronized void setStore(AudioStore s) { store = s; vadBase = (s == null ? 0 : s.streamPos()) - fed; }

    /** 소리 조각을 넣음 (녹음 스레드에서 계속 호출) */
    synchronized void accept(float[] chunk, int n) {
        // VAD는 512개씩 받아야 해서 남는 부분은 다음 조각과 이어 붙임
        float[] all = new float[rest.length + n];
        System.arraycopy(rest, 0, all, 0, rest.length);
        System.arraycopy(chunk, 0, all, rest.length, n);
        int off = 0;
        while (all.length - off >= WINDOW) {
            float[] w = Arrays.copyOfRange(all, off, off + WINDOW);
            off += WINDOW;
            vad.acceptWaveform(w);
            boolean sp = vad.isSpeechDetected();
            if (store != null) store.write(w, WINDOW, sp);
            fed += WINDOW;
            if (sp) {
                if (!speaking) { speaking = true; seg++; curLen = 0; try { listener.onPartial("…"); } catch (Throwable ignored) { } appendCur(preOrdered(), pre.length); lastPartialAt = System.currentTimeMillis(); }
                appendCur(w, WINDOW);
            } else {
                if (speaking) seg++;
                speaking = false;
                for (int i = 0; i < WINDOW; i++) { pre[prePos] = w[i]; prePos = (prePos + 1) % pre.length; }
            }
            drain();
        }
        rest = Arrays.copyOfRange(all, off, all.length);
        // 말하는 동안의 임시 받아 적기는 하지 않음: 문장이 끝난 뒤 한 번만 정확히 받아 적음 (CPU를 아껴 번역이 빨라짐)
    }

    private float[] preOrdered() {
        float[] o = new float[pre.length];
        for (int i = 0; i < pre.length; i++) o[i] = pre[(prePos + i) % pre.length];
        return o;
    }

    private void appendCur(float[] s, int n) {
        if (curLen + n > cur.length) { // 15초를 넘으면 뒤쪽만 남김
            int keep = cur.length - n;
            System.arraycopy(cur, curLen - keep, cur, 0, keep);
            curLen = keep;
        }
        System.arraycopy(s, 0, cur, curLen, n);
        curLen += n;
    }

    /** VAD가 끝난 구간을 내놓으면 글자로 바꾸는 일을 맡김 */
    private void drain() {
        while (!vad.empty()) {
            SpeechSegment seg = vad.front();
            vad.pop();
            final float[] s = seg.getSamples();
            if (s == null || s.length < RATE / 5) continue;
            final int e = epoch;
            long[] where = null;
            if (store != null) {                               // 이 문장의 소리가 저장 파일의 어디에 있는지
                long st = seg.getStart();
                if (st < 0 || st + s.length > fed) st = Math.max(0, fed - s.length);
                long a = vadBase + st, b = a + s.length;
                where = new long[]{store.map(a), store.map(b), store.wallAt(a), store.wallAt(b)};
            }
            final long[] at = where;
            pending.incrementAndGet();
            worker.execute(new Runnable() {
                @Override public void run() {
                    boolean turn = false;
                    try {
                        if (e != epoch) return;
                        float db = rmsDb(s), hz = pitch(s);
                        if (db < -55f) return;                 // 거의 무음
                        if (noDecode) { if (at != null) listener.onFinal("", "", db, hz, s.length / (float) RATE, at); return; }   // 받아 적지 않음: 소리 자리만 알림
                        turn = Heavy.enter(180000);            // 번역과 동시에 돌지 않게 차례를 기다림 (밀린 소리는 버리지 않고 기다렸다가 받아 적음)
                        if (e != epoch) return;
                        String[] r = decode(s);
                        if (!r[0].isEmpty() && e == epoch) listener.onFinal(r[0], r[1], db, hz, s.length / (float) RATE, at);
                    } catch (Throwable ignored) {
                    } finally { Heavy.done(turn); pending.decrementAndGet(); }
                }
            });
        }
    }

    private String[] decode(float[] samples) {
        if (!"whisper".equals(type) || !big()) return decodeOnce(samples);
        String[] r = decodeOnce(padded(samples, PAD1));
        if (suspicious(r[0])) { String[] r2 = decodeOnce(padded(samples, PAD2)); if (!r2[0].isEmpty()) r = r2; }
        return r;
    }

    private String[] decodeOnce(float[] samples) {
        OfflineStream st = rec.createStream();
        try {
            st.acceptWaveform(samples, RATE);
            rec.decode(st);
            OfflineRecognizerResult r = rec.getResult(st);
            String text = r.getText() == null ? "" : r.getText().trim();
            String l = r.getLang() == null ? "" : r.getLang().replaceAll("[^a-zA-Z]", "").toLowerCase();
            return new String[]{text, l};
        } finally { st.release(); }
    }

    /** 말하던 중이면 거기서 끊어 마지막 문장까지 내보냄 */
    synchronized void flush() {
        vad.flush();
        speaking = false; seg++; curLen = 0;
        drain();
    }

    /** 지금까지 쌓인 것을 버림 */
    synchronized void reset() {
        epoch++;
        vad.clear();
        vad.reset();
        speaking = false; seg++; curLen = 0; rest = new float[0];
        fed = 0; vadBase = store == null ? 0 : store.streamPos();
    }

    boolean busy() { return pending.get() > 0; }

    void release() {
        epoch++;
        worker.shutdown();
        try { worker.awaitTermination(3, java.util.concurrent.TimeUnit.SECONDS); } catch (InterruptedException ignored) { }
        try { vad.release(); } catch (Throwable ignored) { }
        try { rec.release(); } catch (Throwable ignored) { }
    }

    // ── 목소리 재기 ──
    static float rmsDb(float[] s) {
        double e = 0;
        for (float v : s) e += v * v;
        double rms = Math.sqrt(e / Math.max(1, s.length));
        return (float) (20 * Math.log10(Math.max(rms, 1e-6)));
    }

    /** 목소리 높낮이(Hz)의 가운데 값. 자기상관으로 60~400Hz 사이를 찾음. 못 찾으면 0 */
    static float pitch(float[] s) {
        final int frame = 640, hop = 320, minLag = RATE / 400, maxLag = RATE / 60;
        float[] f0 = new float[s.length / hop + 1];
        int n = 0;
        for (int start = 0; start + frame + maxLag < s.length; start += hop) {
            double e0 = 0;
            for (int i = 0; i < frame; i++) e0 += s[start + i] * s[start + i];
            if (e0 / frame < 1e-4) continue;                // 조용한 부분은 건너뜀
            double best = 0; int bestLag = 0;
            for (int lag = minLag; lag <= maxLag; lag++) {
                double c = 0, e1 = 0;
                for (int i = 0; i < frame; i++) { c += s[start + i] * s[start + i + lag]; e1 += s[start + i + lag] * s[start + i + lag]; }
                double r = c / Math.sqrt(e0 * e1 + 1e-12);
                if (r > best) { best = r; bestLag = lag; }
            }
            if (best > 0.6 && bestLag > 0) f0[n++] = RATE / (float) bestLag;
        }
        if (n < 3) return 0;
        float[] v = Arrays.copyOf(f0, n);
        Arrays.sort(v);
        return v[n / 2];
    }
}

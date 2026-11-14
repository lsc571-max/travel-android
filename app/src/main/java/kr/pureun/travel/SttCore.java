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
        /** db: 평균 크기(dBFS), hz: 목소리 높낮이(0 = 모름), seconds: 말한 길이 */
        void onFinal(String text, String lang, float db, float hz, float seconds);
    }

    static final int RATE = 16000;
    private static final int WINDOW = 512;

    private final String type;                 // "whisper" | "sensevoice"
    private final String[] files;              // whisper: encoder, decoder, tokens / sensevoice: model, tokens
    private final int threads;
    private final Vad vad;
    private OfflineRecognizer rec;
    private String lang = "ko";
    private final Listener listener;
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
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

    SttCore(String vadModel, String type, String[] files, int threads, float minSilence, Listener l) {
        this.type = type; this.files = files; this.threads = threads; this.listener = l;
        SileroVadModelConfig silero = SileroVadModelConfig.builder()
                .setModel(vadModel).setThreshold(0.5f)
                .setMinSilenceDuration(minSilence).setMinSpeechDuration(0.25f)
                .setWindowSize(WINDOW).setMaxSpeechDuration(10f).build();   // 쉬지 않고 말해도 10초 안에 한 번은 끊어 통역
        vad = new Vad(VadModelConfig.builder().setSileroVadModelConfig(silero)
                .setSampleRate(RATE).setNumThreads(1).setDebug(false).setProvider("cpu").build());
        rec = new OfflineRecognizer(config(lang));
    }

    private OfflineRecognizerConfig config(String language) {
        OfflineModelConfig.Builder m = OfflineModelConfig.builder().setNumThreads(threads).setDebug(false).setProvider("cpu");
        if ("sensevoice".equals(type)) {
            m.setSenseVoice(OfflineSenseVoiceModelConfig.builder().setModel(files[0])
                    .setLanguage(language.isEmpty() ? "auto" : language).setInverseTextNormalization(true).build());
            m.setTokens(files[1]);
        } else {
            m.setWhisper(OfflineWhisperModelConfig.builder().setEncoder(files[0]).setDecoder(files[1])
                    .setLanguage(language).setTask("transcribe").setTailPaddings(200).build());
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
            }
        });
    }

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
            if (sp) {
                if (!speaking) { speaking = true; seg++; curLen = 0; appendCur(preOrdered(), pre.length); lastPartialAt = System.currentTimeMillis(); }
                appendCur(w, WINDOW);
            } else {
                if (speaking) seg++;
                speaking = false;
                for (int i = 0; i < WINDOW; i++) { pre[prePos] = w[i]; prePos = (prePos + 1) % pre.length; }
            }
            drain();
        }
        rest = Arrays.copyOfRange(all, off, all.length);
        // 말하는 동안 1.5초마다 지금까지의 소리를 임시로 글자로 바꿔 보여 줌 (일이 밀려 있으면 건너뜀)
        if (speaking && curLen > RATE && pending.get() == 0 && System.currentTimeMillis() - lastPartialAt > Math.max(1500, partialCost * 3)) {
            lastPartialAt = System.currentTimeMillis();
            final float[] copy = Arrays.copyOfRange(cur, 0, curLen);
            final int e = epoch, g = seg;
            pending.incrementAndGet();
            worker.execute(new Runnable() {
                @Override public void run() {
                    // 그 사이 문장이 끝났으면 건너뜀 → 확정 문장이 중간 글자 때문에 늦어지지 않게
                    try { if (e == epoch && g == seg) { long t0 = System.currentTimeMillis(); String t = decode(copy)[0]; partialCost = System.currentTimeMillis() - t0; if (!t.isEmpty() && e == epoch && g == seg) listener.onPartial(t); } }
                    catch (Throwable ignored) { }
                    finally { pending.decrementAndGet(); }
                }
            });
        }
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
            pending.incrementAndGet();
            worker.execute(new Runnable() {
                @Override public void run() {
                    try {
                        if (e != epoch) return;
                        float db = rmsDb(s), hz = pitch(s);
                        if (db < -55f) return;                 // 거의 무음
                        String[] r = decode(s);
                        if (!r[0].isEmpty() && e == epoch) listener.onFinal(r[0], r[1], db, hz, s.length / (float) RATE);
                    } catch (Throwable ignored) {
                    } finally { pending.decrementAndGet(); }
                }
            });
        }
    }

    private String[] decode(float[] samples) {
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

package kr.pureun.travel;

import android.Manifest;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.util.Base64;
import android.util.Log;

import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayDeque;

/**
 * 끊기지 않는 마이크: 앱이 마이크를 직접 계속 열어 두고(띡 소리 없음), 폰 안 AI(SttCore)로 글자로 바꾼다.
 * 화면(JS)에는 웹 음성 인식과 같은 신호(start/partial/final/end)를 보낸다.
 * AI 통역사용으로 소리를 그대로 흘려보내는 방식(pcm)도 여기서 맡는다.
 * 세션 함수(start/stop/abort/detach)는 UI 스레드에서 부른다.
 */
class LocalStt implements SttCore.Listener {
    private static Boolean libOk;
    private final MainActivity act;

    private SttCore core;
    private String coreModel = "";
    private Thread audio;
    private volatile boolean running, pcm;
    private volatile String lang = "ko";

    private volatile int sid = 0;
    private boolean continuous, discard, started;
    private volatile boolean feeding = true;      // false = 멈추는 중 (더 듣지 않고, 밀린 소리만 끝까지 받아 적음)
    private volatile boolean noDec = false;       // 받아 적지 않고 소리 자리만 알려 주는 방식
    private volatile long sessionFile = 0;        // 이번 세션이 시작될 때 저장 파일의 길이 (이보다 앞의 소리는 앞 세션에서 남은 것)
    private volatile String micPref = "auto";     // 마이크: auto(휴대폰이 알아서) · phone(폰 마이크) · ear(이어폰 마이크)
    private boolean commOn = false;               // 이어폰 마이크용 통화 연결을 켜 둔 상태
    private final java.util.concurrent.atomic.AtomicInteger fileJobs = new java.util.concurrent.atomic.AtomicInteger();   // 저장된 소리를 받아 적는 중인 일
    private volatile AudioStore store;            // 지금 듣는 소리를 저장하는 곳
    static final long KEEP_MS = 5L * 24 * 3600 * 1000;   // 저장한 소리는 5일 뒤 지움
    private final ArrayDeque<Object[]> queue = new ArrayDeque<>();   // 세션이 잠깐 비어 있을 때 나온 문장 {JSON, 시각}
    private Runnable shutdown, release;

    LocalStt(MainActivity a) {
        act = a;
        new Thread(new Runnable() { @Override public void run() { cleanRecs(act); } }, "rec-clean").start();   // 5일 지난 소리 지우기
    }

    static boolean libAvailable() {
        if (libOk == null) {
            try { System.loadLibrary("sherpa-onnx-jni"); libOk = true; }
            catch (Throwable t) { Log.w(MainActivity.TAG, "sherpa lib", t); libOk = false; }
        }
        return libOk;
    }

    private File vadFile() {
        File f = new File(act.getFilesDir(), "silero_vad.onnx");
        if (!f.exists() || f.length() < 1000) {
            try (InputStream in = act.getAssets().open("silero_vad.onnx"); FileOutputStream out = new FileOutputStream(f)) {
                byte[] b = new byte[65536]; int n;
                while ((n = in.read(b)) > 0) out.write(b, 0, n);
            } catch (Throwable t) { f.delete(); return null; }
        }
        return f;
    }

    boolean usable() {
        return libAvailable() && act.models.selected("stt") != null && vadFile() != null;
    }

    String infoJson() {
        try {
            JSONObject o = new JSONObject();
            ModelStore.Model m = act.models.selected("stt");
            o.put("lib", libAvailable());
            o.put("usable", usable());
            o.put("model", m == null ? "" : m.id);
            o.put("langs", m == null ? "" : m.langs);
            o.put("running", running);
            SttCore c = core;
            o.put("busy", c != null && c.busy());      // 아직 받아 적지 못한 소리가 남아 있음
            return o.toString();
        } catch (Exception e) { return "{}"; }
    }

    /** "ko-KR" → "ko", "zh-TW" → "zh", "fil-PH" → "tl", "auto" → "" */
    static String code(String tag) {
        if (tag == null || tag.isEmpty() || tag.startsWith("auto")) return "";
        String c = tag.toLowerCase().split("[-_]")[0];
        return "fil".equals(c) ? "tl" : c;
    }

    // ── 세션 ──
    void start(final int id, final String langTag, final boolean cont) { start(id, langTag, cont, false); }

    /** noDecode: 받아 적지 않고 말소리 구간(저장된 소리의 자리)만 알려 줌 — Gemini가 저장된 소리를 직접 들을 때 */
    void start(final int id, final String langTag, final boolean cont, final boolean noDecode) {
        noDec = noDecode;
        cancelTimers();
        if (pcm) pcmStop();
        if (sid != 0 && sid != id) send(sid, "end", null);   // 앞 세션이 아직 마무리 중이면 끝났다고 알리고 넘어감 (남은 문장은 새 세션으로 감)
        sid = id; continuous = cont; discard = false; started = false; feeding = true;
        lang = code(langTag);
        act.ensurePerms(new String[]{Manifest.permission.RECORD_AUDIO}, new Runnable() {
            @Override public void run() {
                if (sid != id) return;
                if (running) {
                    if (core != null) { core.setLanguage(lang); core.setNoDecode(noDec); }
                    AudioStore st = store;
                    if (st != null) { st.resync(); sessionFile = st.fileSamples(); }
                    started = true;
                    send(id, "start", null);
                    long now = System.currentTimeMillis();
                    while (!queue.isEmpty() && sid == id) {       // 세션이 비어 있던 사이에 나온 문장
                        Object[] q = queue.pollFirst();
                        if (now - (Long) q[1] < 4000) deliver((JSONObject) q[0]);
                    }
                } else startEngine();
            }
        }, new Runnable() {
            @Override public void run() { if (sid == id) { send(id, "error", "not-allowed"); end(id, 0); } }
        });
    }

    /** 말하던 것을 마지막까지 글자로 바꾼 뒤 끝냄 */
    void stop(final int id) {
        if (id != sid) return;
        final SttCore c = core;
        feeding = false;                                   // 더 듣지는 않음
        new Thread(new Runnable() {
            @Override public void run() {
                try {
                    if (c != null && running) {
                        c.flush();
                        // 밀려 있던 소리까지 모두 받아 적을 때까지 기다림 (예전엔 6초만 기다려 뒷부분이 빠질 수 있었음)
                        long until = System.currentTimeMillis() + 30 * 60000;
                        while (c.busy() && sid == id && System.currentTimeMillis() < until) Thread.sleep(50);
                        Thread.sleep(60);
                    }
                } catch (Throwable ignored) { }
                act.ui.post(new Runnable() { @Override public void run() { end(id, 1500); } });
            }
        }, "lstt-stop").start();
    }

    /** 바로 끝냄. 그 사이에 들린 말은 버림 */
    void abort(int id) {
        if (id != sid) return;
        discard = true;
        if (core != null) core.reset();
        queue.clear();
        end(id, 1500);
    }

    /** 화면 쪽 세션만 바꿈 (마이크는 계속 열어 둠, 그 사이 문장은 다음 세션으로 넘김) */
    void detach(int id) {
        if (id != sid) return;
        end(id, 2500);
    }

    private void end(int id, long graceMs) {
        if (id != sid || sid == 0) return;
        send(id, "end", null);
        sid = 0;
        if (graceMs <= 0) { stopEngine(); return; }
        cancelTimers();
        shutdown = new Runnable() { @Override public void run() { if (sid == 0) stopEngine(); } };
        act.ui.postDelayed(shutdown, graceMs);
    }

    private void cancelTimers() {
        if (shutdown != null) { act.ui.removeCallbacks(shutdown); shutdown = null; }
        if (release != null) { act.ui.removeCallbacks(release); release = null; }
    }

    private void send(int id, String type, String text) {
        try {
            JSONObject o = new JSONObject();
            o.put("sid", id); o.put("type", type);
            if (text != null) o.put("text", text);
            act.emit("onStt", o.toString());
        } catch (Exception ignored) { }
    }

    private void deliver(JSONObject o) {
        if (sid == 0) return;
        try {
            o.put("sid", sid); o.put("type", "final");
            act.emit("onStt", o.toString());
        } catch (Exception ignored) { }
        if (!continuous) end(sid, 2500);       // 한 문장씩 듣는 방식: 한 문장 뒤 세션을 끝냄 (마이크는 그대로)
    }

    // ── SttCore에서 오는 결과 (작업 스레드) ──
    @Override public void onPartial(final String text) {
        act.ui.post(new Runnable() { @Override public void run() { if (sid != 0 && started) send(sid, "partial", text); } });
    }

    @Override public void onFinal(final String text, final String l, final float db, final float hz, final float seconds, final long[] at) {
        act.ui.post(new Runnable() {
            @Override public void run() {
                try {
                    JSONObject o = new JSONObject();
                    o.put("text", text); o.put("lang", l); o.put("db", Math.round(db * 10) / 10.0);
                    o.put("hz", Math.round(hz)); o.put("dur", Math.round(seconds * 100) / 100.0);
                    AudioStore st = store;
                    if (at != null && st != null) {            // 이 문장의 소리가 저장된 자리와 들린 시각
                        o.put("f", st.name()); o.put("a", at[0]); o.put("b", at[1]); o.put("t0", at[2]); o.put("t1", at[3]);
                        if (at[0] < sessionFile) o.put("old", true);   // 앞 세션에서 받아 적다 남은 말 → 화면이 지금 말과 섞지 않게
                    }
                    if (sid != 0 && started) deliver(o);
                    else if (!discard && running) { queue.addLast(new Object[]{o, System.currentTimeMillis()}); while (queue.size() > 8) queue.pollFirst(); }
                } catch (Exception ignored) { }
            }
        });
    }

    // ── 마이크 ──
    private void startEngine() {
        running = true;
        MicService.start(act);
        final int id = sid;
        audio = new Thread(new Runnable() { @Override public void run() { loop(id); } }, "lstt-audio");
        audio.start();
    }

    private void loop(final int firstSid) {
        AudioRecord rec = null;
        String err = null;
        try {
            ensureCore();
            core.reset();
            core.setLanguage(lang);
            core.setNoDecode(noDec);
            store = new AudioStore(new File(recDir(act), "L" + new java.text.SimpleDateFormat("yyyyMMdd-HHmmss", java.util.Locale.US).format(new java.util.Date()) + ".pcm"));
            sessionFile = 0;
            core.setStore(store);
            int min = AudioRecord.getMinBufferSize(SttCore.RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
            rec = new AudioRecord(micSource(MediaRecorder.AudioSource.VOICE_RECOGNITION), SttCore.RATE, AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT, Math.max(min, SttCore.RATE));
            if (rec.getState() != AudioRecord.STATE_INITIALIZED) throw new Exception("마이크를 열 수 없습니다");
            applyMic(rec);
            rec.startRecording();
            act.ui.post(new Runnable() {
                @Override public void run() { if (sid != 0) { started = true; send(sid, "start", null); } }
            });
            short[] buf = new short[1600];
            float[] f = new float[1600];
            while (running) {
                int n = rec.read(buf, 0, buf.length);
                if (n < 0) throw new Exception("마이크 읽기 오류 " + n);
                for (int i = 0; i < n; i++) f[i] = buf[i] / 32768f;
                if (n > 0 && feeding) core.accept(f, n);
            }
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "lstt", t);
            err = "audio-capture";
        } finally {
            if (rec != null) { try { rec.stop(); } catch (Throwable ignored) { } try { rec.release(); } catch (Throwable ignored) { } }
            running = false;
            clearMic();
            MicService.stop(act);
            try { if (core != null) core.setStore(null); } catch (Throwable ignored) { }
            AudioStore st = store; store = null;
            if (st != null) st.close();
            cleanRecs(act);
        }
        final String e = err;
        act.ui.post(new Runnable() {
            @Override public void run() {
                queue.clear();
                if (e != null && sid != 0) { int id = sid; send(id, "error", e); send(id, "end", null); sid = 0; }
                // 3분 동안 안 쓰면 모델을 메모리에서 내림
                cancelTimers();
                release = new Runnable() { @Override public void run() { if (!running && fileJobs.get() == 0) releaseCore(); } };
                act.ui.postDelayed(release, 180000);
            }
        });
    }

    private void stopEngine() {
        running = false;
    }

    private void releaseCore() {
        final SttCore c = core;
        core = null; coreModel = "";
        if (c != null) new Thread(new Runnable() { @Override public void run() { try { c.release(); } catch (Throwable ignored) { } } }).start();
    }

    // ── 저장한 소리 (files/rec) ──
    static File recDir(android.content.Context c) { return new File(c.getFilesDir(), "rec"); }

    /** 5일 지난 소리 파일을 지움 (files/rec/keep 안의 것은 남김) */
    static void cleanRecs(android.content.Context c) {
        try {
            File[] list = recDir(c).listFiles();
            if (list == null) return;
            long now = System.currentTimeMillis();
            for (File f : list) if (f.isFile() && now - f.lastModified() > KEEP_MS) f.delete();
        } catch (Throwable ignored) { }
    }

    /** 화면에서 넘겨 준 소리(16kHz·16비트)를 임시 파일(files/rec/T-….pcm)에 적음 — 녹음을 폰 안 AI로 받아 적을 때. first = 새로 쓰기 */
    static boolean recWrite(android.content.Context c, String name, String b64, boolean first) {
        if (name == null || !name.matches("T-[A-Za-z0-9._-]+")) return false;
        try {
            File dir = recDir(c);
            dir.mkdirs();
            try (FileOutputStream out = new FileOutputStream(new File(dir, name), !first)) { out.write(Base64.decode(b64, Base64.DEFAULT)); }
            return true;
        } catch (Throwable t) { return false; }
    }

    /** 저장한 소리의 한 구간을 WAV로 (a·b = 표본 위치, b가 0 이하이면 끝까지). 없으면 null */
    byte[] recWav(android.content.Context c, String name, long a, long b) { return recBytes(c, name, a, b, false); }

    /** raw = true: 머리글(WAV) 없이 소리만 */
    byte[] recBytes(android.content.Context c, String name, long a, long b, boolean raw) {
        if (name == null || !name.matches("[A-Za-z0-9._-]+") || name.contains("..")) return null;
        AudioStore now = store;
        if (now != null && now.name().equals(name)) now.flush();   // 지금 적고 있는 파일이면 방금 소리까지 파일에 내려 적음
        File f = new File(recDir(c), name);
        if (!f.isFile()) f = new File(new File(recDir(c), "keep"), name);
        if (!f.isFile()) return null;
        try (java.io.RandomAccessFile r = new java.io.RandomAccessFile(f, "r")) {
            long total = r.length() / 2;
            if (b <= 0 || b > total) b = total;
            a = Math.max(0, Math.min(a, b));
            long n = Math.min(b - a, 30L * 60 * SttCore.RATE);       // 한 번에 최대 30분
            int bytes = (int) (n * 2);
            if (raw) { byte[] o = new byte[bytes]; r.seek(a * 2); r.readFully(o); return o; }
            ByteBuffer h = ByteBuffer.allocate(44 + bytes).order(ByteOrder.LITTLE_ENDIAN);
            h.put(new byte[]{'R', 'I', 'F', 'F'}).putInt(36 + bytes).put(new byte[]{'W', 'A', 'V', 'E', 'f', 'm', 't', ' '})
                    .putInt(16).putShort((short) 1).putShort((short) 1).putInt(SttCore.RATE).putInt(SttCore.RATE * 2).putShort((short) 2).putShort((short) 16)
                    .put(new byte[]{'d', 'a', 't', 'a'}).putInt(bytes);
            r.seek(a * 2);
            r.readFully(h.array(), 44, bytes);
            return h.array();
        } catch (Throwable t) { return null; }
    }

    /** 모델을 바꾸거나 지웠을 때 */
    void modelChanged() {
        if (!running && fileJobs.get() == 0) releaseCore();
    }

    /** 음성 인식 모델을 메모리에 올림 (처음 한 번, 몇 초). 듣기와 저장된 소리 받아 적기가 함께 씀 */
    private synchronized SttCore ensureCore() throws Exception {
        ModelStore.Model m = act.models.selected("stt");
        File vad = vadFile();
        if (m == null || vad == null || !libAvailable()) throw new Exception("모델 없음");
        if (core == null || !coreModel.equals(m.id)) {
            if (core != null) { try { core.release(); } catch (Throwable ignored) { } core = null; }
            String[] files = new String[m.files.length];
            for (int i = 0; i < files.length; i++) files[i] = act.models.fileOf(m, i).getAbsolutePath();
            int threads = Math.max(2, Math.min(4, Runtime.getRuntime().availableProcessors() - 2));
            core = new SttCore(vad.getAbsolutePath(), m.type, files, threads, 0.7f, this);   // 0.7초 쉬어야 한 문장이 끝난 것으로 봄 (문장 중간에 끊기지 않게)
            coreModel = m.id;
        }
        return core;
    }

    /** 저장해 둔 소리의 한 구간을 폰 안 AI(Whisper)로 받아 적음 → 화면에 onSttFile {id, ok, text|error} */
    void transcribeFile(final int reqId, final String name, final long a, final long b, final String langTag) {
        fileJobs.incrementAndGet();
        new Thread(new Runnable() {
            @Override public void run() {
                try {
                    byte[] raw = recBytes(act, name, a, b, true);
                    if (raw == null || raw.length < 3200) throw new Exception("저장된 소리가 없습니다");
                    float[] s = new float[raw.length / 2];
                    ByteBuffer bb = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
                    for (int i = 0; i < s.length; i++) s[i] = bb.getShort(i * 2) / 32768f;
                    SttCore c = ensureCore();
                    c.transcribe(s, code(langTag), new SttCore.TextCallback() {
                        @Override public void done(String text, String error) { fileJobs.decrementAndGet(); fileResult(reqId, text, error); }
                    });
                } catch (Throwable t) {
                    fileJobs.decrementAndGet();
                    fileResult(reqId, "", t.getMessage() == null ? "받아 적지 못했습니다" : t.getMessage());
                }
            }
        }, "lstt-file").start();
    }

    private void fileResult(int reqId, String text, String error) {
        try {
            JSONObject o = new JSONObject();
            o.put("id", reqId); o.put("ok", error == null); o.put("text", text == null ? "" : text);
            if (error != null) o.put("error", error);
            act.emit("onSttFile", o.toString());
        } catch (Exception ignored) { }
    }

    // ── 마이크 고르기 ──
    void setMic(String pref) { micPref = "phone".equals(pref) || "ear".equals(pref) ? pref : "auto"; }

    private android.media.AudioDeviceInfo inputOf(android.media.AudioManager am, int... types) {
        for (int t : types) for (android.media.AudioDeviceInfo d : am.getDevices(android.media.AudioManager.GET_DEVICES_INPUTS)) if (d.getType() == t) return d;
        return null;
    }

    /** 이어폰 마이크(블루투스)를 쓰려면 통화용 소리 길로 받아야 함 */
    private int micSource(int normal) {
        if (!"ear".equals(micPref)) return normal;
        try {
            android.media.AudioManager am = (android.media.AudioManager) act.getSystemService(android.content.Context.AUDIO_SERVICE);
            if (inputOf(am, android.media.AudioDeviceInfo.TYPE_BLUETOOTH_SCO, 26 /* BLE 헤드셋 */) != null) return MediaRecorder.AudioSource.VOICE_COMMUNICATION;
        } catch (Throwable ignored) { }
        return normal;
    }

    /** 고른 마이크로 듣게 함. 못 찾으면 휴대폰이 알아서 고른 마이크 그대로 */
    private void applyMic(AudioRecord rec) {
        if ("auto".equals(micPref)) return;
        try {
            android.media.AudioManager am = (android.media.AudioManager) act.getSystemService(android.content.Context.AUDIO_SERVICE);
            if ("phone".equals(micPref)) {
                android.media.AudioDeviceInfo d = inputOf(am, android.media.AudioDeviceInfo.TYPE_BUILTIN_MIC);
                if (d != null) rec.setPreferredDevice(d);
                return;
            }
            android.media.AudioDeviceInfo bt = inputOf(am, android.media.AudioDeviceInfo.TYPE_BLUETOOTH_SCO, 26);
            if (bt != null) {                                   // 블루투스 이어폰: 통화용 연결을 켜야 이어폰 마이크가 열림
                if (android.os.Build.VERSION.SDK_INT >= 31) {
                    for (android.media.AudioDeviceInfo c : am.getAvailableCommunicationDevices()) {
                        if (c.getType() == android.media.AudioDeviceInfo.TYPE_BLUETOOTH_SCO || c.getType() == 26) { commOn = am.setCommunicationDevice(c); break; }
                    }
                } else { am.startBluetoothSco(); am.setBluetoothScoOn(true); commOn = true; }
                rec.setPreferredDevice(bt);
                return;
            }
            android.media.AudioDeviceInfo w = inputOf(am, android.media.AudioDeviceInfo.TYPE_WIRED_HEADSET, android.media.AudioDeviceInfo.TYPE_USB_HEADSET);
            if (w != null) rec.setPreferredDevice(w);
        } catch (Throwable t) { Log.w(MainActivity.TAG, "mic", t); }
    }

    private void clearMic() {
        if (!commOn) return;
        commOn = false;
        try {
            android.media.AudioManager am = (android.media.AudioManager) act.getSystemService(android.content.Context.AUDIO_SERVICE);
            if (android.os.Build.VERSION.SDK_INT >= 31) am.clearCommunicationDevice();
            else { am.setBluetoothScoOn(false); am.stopBluetoothSco(); }
        } catch (Throwable ignored) { }
    }

    void destroy() {
        sid = 0; running = false; pcm = false;
        cancelTimers();
        releaseCore();
    }

    // ── AI 통역사용: 마이크 소리를 0.1초 조각으로 그대로 화면(JS)에 넘김 ──
    void pcmStart(final boolean echoCancel) {
        if (pcm) return;
        if (sid != 0) abort(sid);
        running = false;
        act.ensurePerms(new String[]{Manifest.permission.RECORD_AUDIO}, new Runnable() {
            @Override public void run() {
                pcm = true;
                MicService.start(act);
                new Thread(new Runnable() { @Override public void run() { pcmLoop(echoCancel); } }, "pcm-audio").start();
            }
        }, new Runnable() {
            @Override public void run() { act.emit("onPcmEnd", "\"not-allowed\""); }
        });
    }

    void pcmStop() { pcm = false; }

    private void pcmLoop(boolean echoCancel) {
        AudioRecord rec = null;
        String err = "";
        try {
            Thread.sleep(150);                                   // 앞서 쓰던 마이크가 닫힐 시간
            int min = AudioRecord.getMinBufferSize(SttCore.RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
            rec = new AudioRecord(micSource(echoCancel ? MediaRecorder.AudioSource.VOICE_COMMUNICATION : MediaRecorder.AudioSource.VOICE_RECOGNITION),
                    SttCore.RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, Math.max(min, SttCore.RATE));
            if (rec.getState() != AudioRecord.STATE_INITIALIZED) throw new Exception("마이크를 열 수 없습니다");
            applyMic(rec);
            rec.startRecording();
            short[] buf = new short[1600];
            ByteBuffer bb = ByteBuffer.allocate(3200).order(ByteOrder.LITTLE_ENDIAN);
            while (pcm) {
                int n = rec.read(buf, 0, buf.length);
                if (n < 0) throw new Exception("마이크 읽기 오류 " + n);
                if (n == 0) continue;
                bb.clear();
                for (int i = 0; i < n; i++) bb.putShort(buf[i]);
                act.emit("onPcm", "\"" + Base64.encodeToString(bb.array(), 0, n * 2, Base64.NO_WRAP) + "\"");
            }
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "pcm", t);
            err = "audio-capture";
        } finally {
            if (rec != null) { try { rec.stop(); } catch (Throwable ignored) { } try { rec.release(); } catch (Throwable ignored) { } }
            pcm = false;
            clearMic();
            if (!running) MicService.stop(act);
        }
        act.emit("onPcmEnd", "\"" + err + "\"");
    }
}

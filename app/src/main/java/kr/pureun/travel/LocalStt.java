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

    private int sid = 0;
    private boolean continuous, discard, started;
    private final ArrayDeque<Object[]> queue = new ArrayDeque<>();   // 세션이 잠깐 비어 있을 때 나온 문장 {JSON, 시각}
    private Runnable shutdown, release;

    LocalStt(MainActivity a) { act = a; }

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
    void start(final int id, final String langTag, final boolean cont) {
        cancelTimers();
        if (pcm) pcmStop();
        sid = id; continuous = cont; discard = false; started = false;
        lang = code(langTag);
        act.ensurePerms(new String[]{Manifest.permission.RECORD_AUDIO}, new Runnable() {
            @Override public void run() {
                if (sid != id) return;
                if (running) {
                    if (core != null) core.setLanguage(lang);
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
        new Thread(new Runnable() {
            @Override public void run() {
                try {
                    if (c != null && running) {
                        c.flush();
                        long until = System.currentTimeMillis() + 6000;
                        while (c.busy() && System.currentTimeMillis() < until) Thread.sleep(50);
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

    @Override public void onFinal(final String text, final String l, final float db, final float hz, final float seconds) {
        act.ui.post(new Runnable() {
            @Override public void run() {
                try {
                    JSONObject o = new JSONObject();
                    o.put("text", text); o.put("lang", l); o.put("db", Math.round(db * 10) / 10.0);
                    o.put("hz", Math.round(hz)); o.put("dur", Math.round(seconds * 100) / 100.0);
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
            ModelStore.Model m = act.models.selected("stt");
            File vad = vadFile();
            if (m == null || vad == null || !libAvailable()) throw new Exception("모델 없음");
            if (core == null || !coreModel.equals(m.id)) {            // 모델 불러오기 (처음 한 번, 몇 초)
                if (core != null) { try { core.release(); } catch (Throwable ignored) { } core = null; }
                String[] files = new String[m.files.length];
                for (int i = 0; i < files.length; i++) files[i] = act.models.fileOf(m, i).getAbsolutePath();
                int threads = Math.max(2, Math.min(4, Runtime.getRuntime().availableProcessors() - 2));
                core = new SttCore(vad.getAbsolutePath(), m.type, files, threads, 0.7f, this);   // 0.7초 쉬어야 한 문장이 끝난 것으로 봄 (문장 중간에 끊기지 않게)
                coreModel = m.id;
            }
            core.reset();
            core.setLanguage(lang);
            int min = AudioRecord.getMinBufferSize(SttCore.RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
            rec = new AudioRecord(MediaRecorder.AudioSource.VOICE_RECOGNITION, SttCore.RATE, AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT, Math.max(min, SttCore.RATE));
            if (rec.getState() != AudioRecord.STATE_INITIALIZED) throw new Exception("마이크를 열 수 없습니다");
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
                if (n > 0) core.accept(f, n);
            }
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "lstt", t);
            err = "audio-capture";
        } finally {
            if (rec != null) { try { rec.stop(); } catch (Throwable ignored) { } try { rec.release(); } catch (Throwable ignored) { } }
            running = false;
            MicService.stop(act);
        }
        final String e = err;
        act.ui.post(new Runnable() {
            @Override public void run() {
                queue.clear();
                if (e != null && sid != 0) { int id = sid; send(id, "error", e); send(id, "end", null); sid = 0; }
                // 3분 동안 안 쓰면 모델을 메모리에서 내림
                cancelTimers();
                release = new Runnable() { @Override public void run() { if (!running) releaseCore(); } };
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

    /** 모델을 바꾸거나 지웠을 때 */
    void modelChanged() {
        if (!running) releaseCore();
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
            rec = new AudioRecord(echoCancel ? MediaRecorder.AudioSource.VOICE_COMMUNICATION : MediaRecorder.AudioSource.VOICE_RECOGNITION,
                    SttCore.RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, Math.max(min, SttCore.RATE));
            if (rec.getState() != AudioRecord.STATE_INITIALIZED) throw new Exception("마이크를 열 수 없습니다");
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
            if (!running) MicService.stop(act);
        }
        act.emit("onPcmEnd", "\"" + err + "\"");
    }
}

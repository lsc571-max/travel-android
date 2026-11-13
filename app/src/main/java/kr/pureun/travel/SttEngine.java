package kr.pureun.travel;

import android.Manifest;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.util.Log;

import org.json.JSONObject;

import java.util.ArrayList;

/**
 * 음성 인식: 휴대폰의 음성 인식기(구글)를 웹의 SpeechRecognition처럼 쓰게 해 준다.
 * 한 번에 한 세션만 듣는다. continuous=true면 문장이 끝나도 이어서 다시 듣는다.
 * 모든 메서드는 UI 스레드에서 실행된다.
 */
class SttEngine implements RecognitionListener {
    private final MainActivity act;
    private SpeechRecognizer rec;
    private boolean recOffline;

    private int sid = 0;            // 지금 세션 번호 (0 = 없음)
    private String lang = "ko-KR";
    private boolean continuous, offline, stopping, started;
    private int busyRetry;
    private long listenAt;
    private String lastPartial = "";

    SttEngine(MainActivity a) { act = a; }

    boolean offlineAvailable() {
        try {
            return Build.VERSION.SDK_INT >= 31 && SpeechRecognizer.isOnDeviceRecognitionAvailable(act);
        } catch (Throwable t) { return false; }
    }

    boolean available() {
        try { return SpeechRecognizer.isRecognitionAvailable(act); } catch (Throwable t) { return false; }
    }

    void start(final int id, final String language, final boolean cont, final boolean preferOffline) {
        if (sid != 0) {                            // 앞 세션이 남아 있으면 정리
            try { if (rec != null) rec.cancel(); } catch (Exception ignored) { }
            finish(sid, null, true);
        }
        sid = id; lang = language; continuous = cont; offline = preferOffline && offlineAvailable();
        stopping = false; started = false; busyRetry = 0; lastPartial = "";
        act.ensurePerms(new String[]{Manifest.permission.RECORD_AUDIO}, new Runnable() {
            @Override public void run() { if (sid == id) listen(); }
        }, new Runnable() {
            @Override public void run() { if (sid == id) finish(id, "not-allowed", false); }
        });
    }

    void stop(final int id) {
        if (id != sid) return;
        stopping = true;
        try { if (rec != null) rec.stopListening(); } catch (Exception ignored) { }
        // 결과가 안 오면 1.5초 뒤 끝냄
        act.ui.postDelayed(new Runnable() {
            @Override public void run() { if (sid == id) finish(id, null, true); }
        }, 1500);
    }

    void abort(int id) {
        if (id != sid) return;
        try { if (rec != null) rec.cancel(); } catch (Exception ignored) { }
        finish(id, null, false);
    }

    void destroy() {
        sid = 0;
        try { if (rec != null) rec.destroy(); } catch (Exception ignored) { }
        rec = null;
    }

    private void listen() {
        try {
            if (rec == null || recOffline != offline) {
                if (rec != null) try { rec.destroy(); } catch (Exception ignored) { }
                rec = (offline && Build.VERSION.SDK_INT >= 31)
                        ? SpeechRecognizer.createOnDeviceSpeechRecognizer(act)
                        : SpeechRecognizer.createSpeechRecognizer(act);
                recOffline = offline;
                rec.setRecognitionListener(this);
            }
            Intent i = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
            i.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
            i.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang);
            i.putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, lang);
            i.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true);
            i.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1);
            i.putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, act.getPackageName());
            if (offline) i.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true);
            lastPartial = "";
            try { rec.cancel(); } catch (Exception ignored) { }
            listenAt = System.currentTimeMillis();
            rec.startListening(i);
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "stt start", t);
            finish(sid, "service-not-allowed", false);
        }
    }

    private void send(String type, String text) {
        if (sid == 0) return;
        try {
            JSONObject o = new JSONObject();
            o.put("sid", sid); o.put("type", type);
            if (text != null) o.put("text", text);
            act.emit("onStt", o.toString());
        } catch (Exception ignored) { }
    }

    /** 세션 끝: (keepPartial이면) 남은 중간 글자를 확정으로 보내고 end */
    private void finish(int id, String error, boolean keepPartial) {
        if (id != sid || sid == 0) return;
        if (keepPartial && !lastPartial.isEmpty()) send("final", lastPartial);
        lastPartial = "";
        if (error != null) send("error", error);
        send("end", null);
        sid = 0;
    }

    private static String first(Bundle b) {
        if (b == null) return "";
        ArrayList<String> l = b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
        String s = (l != null && !l.isEmpty() && l.get(0) != null) ? l.get(0) : "";
        return s.trim();
    }

    @Override public void onReadyForSpeech(Bundle params) {
        if (!started) { started = true; send("start", null); }
    }

    @Override public void onBeginningOfSpeech() { send("speechstart", null); }

    @Override public void onRmsChanged(float rmsdB) { }

    @Override public void onBufferReceived(byte[] buffer) { }

    @Override public void onEndOfSpeech() { send("speechend", null); }

    @Override public void onPartialResults(Bundle partialResults) {
        String s = first(partialResults);
        if (partialResults != null) {
            ArrayList<String> un = partialResults.getStringArrayList("android.speech.extra.UNSTABLE_TEXT");
            if (un != null && !un.isEmpty() && un.get(0) != null && !un.get(0).trim().isEmpty())
                s = (s + " " + un.get(0).trim()).trim();
        }
        if (s.isEmpty()) return;
        lastPartial = s;
        send("partial", s);
    }

    @Override public void onResults(Bundle results) {
        String s = first(results);
        if (s.isEmpty()) s = lastPartial;
        lastPartial = "";
        if (!s.isEmpty()) send("final", s);
        next();
    }

    @Override public void onError(int error) {
        final int id = sid;
        if (id == 0) return;
        switch (error) {
            case SpeechRecognizer.ERROR_NO_MATCH:
            case SpeechRecognizer.ERROR_SPEECH_TIMEOUT:
                next();
                return;
            case SpeechRecognizer.ERROR_RECOGNIZER_BUSY:
                if (busyRetry++ < 4 && !stopping) {
                    try { rec.cancel(); } catch (Exception ignored) { }
                    act.ui.postDelayed(new Runnable() {
                        @Override public void run() { if (sid == id) listen(); }
                    }, 350);
                    return;
                }
                finish(id, "aborted", true);
                return;
            case SpeechRecognizer.ERROR_CLIENT:
                if (System.currentTimeMillis() - listenAt < 500) return; // 방금 끊은 앞 세션의 뒤늦은 신호
                finish(id, null, true);
                return;
            case SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS:
                finish(id, "not-allowed", false);
                return;
            case SpeechRecognizer.ERROR_AUDIO:
                finish(id, "audio-capture", true);
                return;
            case SpeechRecognizer.ERROR_NETWORK:
            case SpeechRecognizer.ERROR_NETWORK_TIMEOUT:
            case SpeechRecognizer.ERROR_SERVER:
                finish(id, "network", true);
                return;
            default:
                // 12: 지원하지 않는 언어, 13: 언어 팩 없음 등
                finish(id, error == 12 || error == 13 ? "language-not-supported" : "service-not-allowed", false);
        }
    }

    @Override public void onEvent(int eventType, Bundle params) { }

    /** 한 문장이 끝난 뒤: 이어 듣기면 다시 듣고, 아니면 세션 끝 */
    private void next() {
        final int id = sid;
        if (id == 0) return;
        if (continuous && !stopping) {
            busyRetry = 0;
            act.ui.post(new Runnable() {
                @Override public void run() { if (sid == id && !stopping) listen(); }
            });
        } else finish(id, null, true);
    }
}

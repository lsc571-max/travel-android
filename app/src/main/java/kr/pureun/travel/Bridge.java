package kr.pureun.travel;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.util.Log;
import android.webkit.JavascriptInterface;

import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** 화면(JS)에서 부르는 창구. window.AndroidBridge.xxx() */
class Bridge {
    private final MainActivity act;
    private final ExecutorService llmPool = Executors.newSingleThreadExecutor();
    private OutputStream saveOut;
    private Uri saveUri;
    private String saveName = "";

    Bridge(MainActivity a) { act = a; }

    @JavascriptInterface
    public String info() {
        try {
            JSONObject o = new JSONObject();
            o.put("version", act.getPackageManager().getPackageInfo(act.getPackageName(), 0).versionName);
            o.put("sdk", Build.VERSION.SDK_INT);
            o.put("device", Build.MANUFACTURER + " " + Build.MODEL);
            o.put("stt", act.stt.available());
            o.put("sttOffline", act.stt.offlineAvailable());
            o.put("llmEngine", act.llm.available());
            return o.toString();
        } catch (Exception e) { return "{}"; }
    }

    // ── 음성 인식 ──
    @JavascriptInterface
    public void sttStart(final int sid, final String lang, final boolean continuous, final boolean preferOffline) {
        act.ui.post(new Runnable() { @Override public void run() { act.stt.start(sid, lang, continuous, preferOffline); } });
    }

    @JavascriptInterface
    public void sttStop(final int sid) {
        act.ui.post(new Runnable() { @Override public void run() { act.stt.stop(sid); } });
    }

    @JavascriptInterface
    public void sttAbort(final int sid) {
        act.ui.post(new Runnable() { @Override public void run() { act.stt.abort(sid); } });
    }

    // ── 끊기지 않는 마이크 (폰 안 음성 인식) ──
    @JavascriptInterface
    public String lsttInfo() { return act.lstt.infoJson(); }

    @JavascriptInterface
    public void lsttStart(final int sid, final String lang, final boolean continuous) {
        act.ui.post(new Runnable() { @Override public void run() { act.lstt.start(sid, lang, continuous); } });
    }

    /** noDecode = true: 받아 적지 않고 말소리 구간(저장된 소리의 자리)만 알려 줌 (Gemini가 소리를 직접 들을 때) */
    @JavascriptInterface
    public void lsttStart2(final int sid, final String lang, final boolean continuous, final boolean noDecode) {
        act.ui.post(new Runnable() { @Override public void run() { act.lstt.start(sid, lang, continuous, noDecode); } });
    }

    /** 저장해 둔 소리(name 파일의 a~b 표본)를 폰 안 AI로 받아 적음 → onSttFile */
    @JavascriptInterface
    public void lsttFile(final int reqId, final String name, final String a, final String b, final String lang) {
        long x = 0, y = 0;
        try { x = Long.parseLong(a); y = Long.parseLong(b); } catch (Exception ignored) { }
        act.lstt.transcribeFile(reqId, name, x, y, lang);
    }

    /** 저장한 기록이 쓰는 소리 파일을 5일 뒤에도 지우지 않게 (on) / 다시 지워도 되게 (off) */
    @JavascriptInterface
    public void recKeep(String name, boolean on) { LocalStt.recKeep(act, name, on); }

    /** 들은 소리 파일 목록(걷어낸 파일·원본)과 남은 저장 공간 */
    @JavascriptInterface
    public String recFiles() { return act.lstt.recFilesJson(); }

    /** 들은 소리 파일 하나 지우기 (L… 걷어낸 파일 · R… 원본) */
    @JavascriptInterface
    public boolean recDelete(String name) { return act.lstt.recDelete(name); }

    /** 마이크 고르기: "auto" · "phone" · "ear" */
    @JavascriptInterface
    public void setMic(String pref) { act.lstt.setMic(pref); }

    /** 듣는 소리 고르기: "mic" 마이크 · "sys" 폰에서 나오는 소리 · "sysq" 폰 소리(스피커·이어폰으로는 소리 없이) */
    @JavascriptInterface
    public void setCapture(String src) { act.lstt.setCapture(src); }

    /** 듣기 모드의 녹음인지 (true = 원본도 따로 적고 저절로 지우지 않음) */
    @JavascriptInterface
    public void setKeepRec(boolean on) { act.lstt.setKeepRec(on); }

    /** how: "stop" 마지막까지 받아 적고 끝 · "abort" 버리고 끝 · "detach" 마이크는 두고 세션만 끝 */
    @JavascriptInterface
    public void lsttEnd(final int sid, final String how) {
        act.ui.post(new Runnable() {
            @Override public void run() {
                if ("stop".equals(how)) act.lstt.stop(sid);
                else if ("detach".equals(how)) act.lstt.detach(sid);
                else act.lstt.abort(sid);
            }
        });
    }

    /** AI 통역사: 마이크 소리를 그대로 화면으로 흘려보내기 */
    @JavascriptInterface
    public void pcmStart(final boolean echoCancel) {
        act.ui.post(new Runnable() { @Override public void run() { act.lstt.pcmStart(echoCancel); } });
    }

    @JavascriptInterface
    public void pcmStop() { act.lstt.pcmStop(); }

    /** 이어폰(유선·블루투스)이 연결돼 있는지 */
    @JavascriptInterface
    public boolean headset() {
        try {
            android.media.AudioManager am = (android.media.AudioManager) act.getSystemService(Context.AUDIO_SERVICE);
            for (android.media.AudioDeviceInfo d : am.getDevices(android.media.AudioManager.GET_DEVICES_OUTPUTS)) {
                int t = d.getType();
                if (t == android.media.AudioDeviceInfo.TYPE_WIRED_HEADSET || t == android.media.AudioDeviceInfo.TYPE_WIRED_HEADPHONES
                        || t == android.media.AudioDeviceInfo.TYPE_BLUETOOTH_A2DP || t == android.media.AudioDeviceInfo.TYPE_BLUETOOTH_SCO
                        || t == android.media.AudioDeviceInfo.TYPE_USB_HEADSET || t == 26 /* BLE 헤드셋 */)
                    return true;
            }
        } catch (Throwable ignored) { }
        return false;
    }

    /** 화면이 꺼져도 계속 듣게 할지 (듣기 모드 + 폰 안 음성 인식일 때 화면 쪽에서 켬) */
    @JavascriptInterface
    public void setBackground(boolean on) { act.bgKeep = on; }

    /** 통역 소리를 읽는 중인지 (읽는 동안에는 화면이 꺼져도 멈추지 않게) */
    @JavascriptInterface
    public void setPlaying(final boolean on) {
        act.playKeep = on;
        act.runOnUiThread(new Runnable() { @Override public void run() { if (on) PlayService.start(act); else PlayService.stop(act); } });
    }

    // ── 목소리 ──
    @JavascriptInterface
    public String ttsVoices() { return act.tts.voices(); }

    /** 폰의 음성 데이터 설치 화면을 엶 (고품질 음성 받기). 못 열면 글자 읽어주기 설정 화면, 그것도 안 되면 false */
    @JavascriptInterface
    public boolean ttsInstall() {
        String eng = act.tts.engine();
        Intent[] tries = {
            eng == null ? null : new Intent(android.speech.tts.TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA).setPackage(eng),
            new Intent(android.speech.tts.TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA),
            new Intent("com.android.settings.TTS_SETTINGS")
        };
        for (Intent i : tries) {
            if (i == null) continue;
            try { act.startActivity(i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)); return true; } catch (Throwable t) { Log.w(MainActivity.TAG, "ttsInstall", t); }
        }
        return false;
    }

    @JavascriptInterface
    public void ttsSpeak(final int id, final String text, final String lang, final float rate, final String voice, final float volume) {
        act.ui.post(new Runnable() { @Override public void run() { act.tts.speak(id, text, lang, rate, voice, volume); } });
    }

    @JavascriptInterface
    public void ttsCancel() {
        act.ui.post(new Runnable() { @Override public void run() { act.tts.cancel(); } });
    }

    // ── 폰 안 번역 AI ──
    @JavascriptInterface
    public String llmState() { return act.llm.stateJson(); }

    @JavascriptInterface
    public void llmEnsure() {
        llmPool.execute(new Runnable() { @Override public void run() { act.llm.ensure(); } });
    }

    @JavascriptInterface
    public void llmStop() {
        llmPool.execute(new Runnable() { @Override public void run() { act.llm.stop(); } });
    }

    @JavascriptInterface
    public void llmChat(final int reqId, final String bodyJson) {
        llmPool.execute(new Runnable() {
            @Override public void run() {
                JSONObject o = new JSONObject();
                try {
                    o.put("id", reqId);
                    try {
                        o.put("text", act.llm.chat(bodyJson, new Runnable() {
                            @Override public void run() { act.emit("onLlm", "{\"id\":" + reqId + ",\"started\":true}"); }
                        }));
                        o.put("ok", true);
                    } catch (Throwable t) {
                        o.put("ok", false);
                        o.put("error", t.getMessage() == null ? t.getClass().getSimpleName() : t.getMessage());
                    }
                } catch (Exception ignored) { }
                act.emit("onLlm", o.toString());
            }
        });
    }

    @JavascriptInterface
    public String models() { return act.models.listJson(); }

    @JavascriptInterface
    public void modelDownload(String id) { act.models.download(id); }

    @JavascriptInterface
    public void modelCancel(String id) { act.models.cancel(id); }

    @JavascriptInterface
    public void modelDelete(final String id) {
        llmPool.execute(new Runnable() {
            @Override public void run() {
                ModelStore.Model m = act.models.find(id);
                if (m == null) return;
                if ("mt".equals(m.kind)) {
                    if (id.equals(act.models.selectedId("mt"))) act.llm.stop();
                    act.models.delete(id);
                    act.emit("onLlmState", act.llm.stateJson());
                } else {
                    act.models.delete(id);
                    act.ui.post(new Runnable() { @Override public void run() { act.lstt.modelChanged(); } });
                }
            }
        });
    }

    @JavascriptInterface
    public void modelSelect(final String id) {
        llmPool.execute(new Runnable() {
            @Override public void run() {
                ModelStore.Model m = act.models.find(id);
                if (m == null) return;
                act.models.select(id);
                if ("mt".equals(m.kind)) act.llm.ensure();
                else act.ui.post(new Runnable() { @Override public void run() { act.lstt.modelChanged(); } });
            }
        });
    }

    @JavascriptInterface
    public String modelAdd(String name, String url) { return act.models.addCustom(name, url); }

    // ── 공유·복사·붙여넣기 ──
    @JavascriptInterface
    public void share(final String title, final String text) {
        act.ui.post(new Runnable() {
            @Override public void run() {
                try {
                    Intent i = new Intent(Intent.ACTION_SEND);
                    i.setType("text/plain");
                    i.putExtra(Intent.EXTRA_SUBJECT, title);
                    i.putExtra(Intent.EXTRA_TEXT, text);
                    act.startActivity(Intent.createChooser(i, title));
                } catch (Exception e) { Log.w(MainActivity.TAG, "share", e); }
            }
        });
    }

    @JavascriptInterface
    public void copy(final String text) {
        act.ui.post(new Runnable() {
            @Override public void run() {
                try {
                    ClipboardManager cm = (ClipboardManager) act.getSystemService(Context.CLIPBOARD_SERVICE);
                    cm.setPrimaryClip(ClipData.newPlainText("text", text));
                } catch (Exception ignored) { }
            }
        });
    }

    @JavascriptInterface
    public String paste() {
        try {
            ClipboardManager cm = (ClipboardManager) act.getSystemService(Context.CLIPBOARD_SERVICE);
            ClipData d = cm.getPrimaryClip();
            if (d == null || d.getItemCount() == 0) return "";
            CharSequence t = d.getItemAt(0).coerceToText(act);
            return t == null ? "" : t.toString();
        } catch (Throwable t) { return ""; }
    }

    // ── 다른 앱(제미나이 · Claude)으로 넘기기 ──
    private Intent forApp(Intent i, String pkgs) {
        if (pkgs == null) return null;
        for (String p : pkgs.split(",")) {
            p = p.trim();
            if (p.isEmpty()) continue;
            try {
                Intent t = new Intent(i).setPackage(p);
                if (t.resolveActivity(act.getPackageManager()) != null) return t;
            } catch (Throwable ignored) { }
        }
        return null;
    }

    /** 글(지시문)을 그 앱에 바로 넘김. pkgs = 앱 이름표(패키지)를 쉼표로. 넘길 수 있으면 true (못 넘기면 화면이 복사 + 앱 열기로 대신함) */
    @JavascriptInterface
    public boolean sendText(String pkgs, String text) {
        try {
            Intent i = new Intent(Intent.ACTION_SEND);
            i.setType("text/plain");
            i.putExtra(Intent.EXTRA_TEXT, text);
            final Intent t = forApp(i, pkgs);
            if (t == null) return false;
            t.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            act.ui.post(new Runnable() { @Override public void run() { try { act.startActivity(t); } catch (Throwable e) { Log.w(MainActivity.TAG, "sendText", e); } } });
            return true;
        } catch (Throwable t) { Log.w(MainActivity.TAG, "sendText", t); return false; }
    }

    /** 그 앱을 엶. 설치되어 있지 않으면 false */
    @JavascriptInterface
    public boolean openApp(String pkgs) {
        try {
            for (String p : pkgs.split(",")) {
                final Intent i = act.getPackageManager().getLaunchIntentForPackage(p.trim());
                if (i == null) continue;
                act.ui.post(new Runnable() { @Override public void run() { try { act.startActivity(i); } catch (Throwable e) { Log.w(MainActivity.TAG, "openApp", e); } } });
                return true;
            }
        } catch (Throwable t) { Log.w(MainActivity.TAG, "openApp", t); }
        return false;
    }

    /**
     * 들은 소리의 한 구간(파일 name의 a~b 표본)을 WAV 파일로 만들어 그 앱에 넘김 (지시문 text도 함께).
     * 끝나면 화면에 onSendAudio {id, ok, how: "app" | "menu", error}
     */
    @JavascriptInterface
    public void sendAudio(final int id, final String pkgs, final String name, final String a, final String b, final String text) {
        try {
            org.json.JSONArray one = new org.json.JSONArray();
            one.put(new org.json.JSONArray().put(name).put(Long.parseLong(a)).put(Long.parseLong(b)));
            sendAudios(id, pkgs, one.toString(), text);
        } catch (Throwable t) { sendResult(id, "", "소리 자리가 올바르지 않습니다"); }
    }

    /**
     * 들은 소리 여러 구간을 차례로 WAV 파일(01-…, 02-… 순서)로 만들어 한꺼번에 그 앱에 넘김. list = [[파일, a, b], …] (JSON).
     * 파일은 내려받기 폴더(Download/TravelInterpreter)에 만들고, 하루 지난 것은 다음에 보낼 때 지움.
     * 그 앱이 소리 파일을 받지 못하면 공유 메뉴를 띄움. 끝나면 화면에 onSendAudio {id, ok, how, error}
     */
    @JavascriptInterface
    public void sendAudios(final int id, final String pkgs, final String list, final String text) {
        new Thread(new Runnable() {
            @Override public void run() {
                String err = null, how = "";
                try {
                    if (Build.VERSION.SDK_INT < 29) throw new Exception("안드로이드 10 이상에서만 됩니다");
                    org.json.JSONArray arr = new org.json.JSONArray(list);
                    if (arr.length() == 0) throw new Exception("보낼 소리가 없습니다");
                    String dirPath = Environment.DIRECTORY_DOWNLOADS + "/TravelInterpreter";
                    try {                                          // 예전에 보내려고 만든 파일(하루 지난 것)은 지움
                        act.getContentResolver().delete(MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                                MediaStore.Downloads.RELATIVE_PATH + " LIKE ? AND " + MediaStore.Downloads.DATE_ADDED + " < ?",
                                new String[]{dirPath + "%", String.valueOf(System.currentTimeMillis() / 1000 - 24 * 3600)});
                    } catch (Throwable ignored) { }
                    String stamp = new java.text.SimpleDateFormat("MMdd-HHmmss", java.util.Locale.US).format(new java.util.Date());
                    final java.util.ArrayList<Uri> uris = new java.util.ArrayList<>();
                    for (int k = 0; k < arr.length(); k++) {
                        org.json.JSONArray it = arr.getJSONArray(k);
                        byte[] wav = act.lstt.recWav(act, it.getString(0), it.getLong(1), it.getLong(2));
                        if (wav == null || wav.length < 3244) throw new Exception("저장된 소리가 없습니다 (" + (k + 1) + "번째)");
                        ContentValues v = new ContentValues();
                        v.put(MediaStore.Downloads.DISPLAY_NAME, String.format(java.util.Locale.US, "%02d-travel-%s.wav", k + 1, stamp));
                        v.put(MediaStore.Downloads.MIME_TYPE, "audio/x-wav");
                        v.put(MediaStore.Downloads.RELATIVE_PATH, dirPath);
                        v.put(MediaStore.Downloads.IS_PENDING, 1);
                        Uri uri = act.getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                        if (uri == null) throw new Exception("파일을 만들지 못했습니다");
                        try (OutputStream os = act.getContentResolver().openOutputStream(uri)) { os.write(wav); }
                        ContentValues done = new ContentValues();
                        done.put(MediaStore.Downloads.IS_PENDING, 0);
                        act.getContentResolver().update(uri, done, null, null);
                        uris.add(uri);
                    }
                    Intent i;
                    if (uris.size() == 1) {
                        i = new Intent(Intent.ACTION_SEND);
                        i.putExtra(Intent.EXTRA_STREAM, uris.get(0));
                    } else {                                       // 여러 개: 1번, 2번, 3번 … 순서대로 한꺼번에
                        i = new Intent(Intent.ACTION_SEND_MULTIPLE);
                        i.putParcelableArrayListExtra(Intent.EXTRA_STREAM, uris);
                    }
                    i.setType("audio/x-wav");
                    i.putExtra(Intent.EXTRA_TEXT, text);
                    android.content.ClipData clip = android.content.ClipData.newRawUri("", uris.get(0));
                    for (int k = 1; k < uris.size(); k++) clip.addItem(new android.content.ClipData.Item(uris.get(k)));
                    i.setClipData(clip);                           // 받는 앱이 파일을 모두 읽을 수 있게
                    i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    Intent t = forApp(i, pkgs);
                    how = t != null ? "app" : "menu";
                    final Intent go = t != null ? t : Intent.createChooser(i, "소리 파일 보내기");
                    go.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    act.ui.post(new Runnable() { @Override public void run() { try { act.startActivity(go); } catch (Throwable e) { Log.w(MainActivity.TAG, "sendAudio", e); } } });
                } catch (Throwable t) {
                    Log.w(MainActivity.TAG, "sendAudio", t);
                    err = t.getMessage() == null ? t.getClass().getSimpleName() : t.getMessage();
                }
                sendResult(id, how, err);
            }
        }, "send-audio").start();
    }

    private void sendResult(int id, String how, String err) {
        try {
            JSONObject o = new JSONObject();
            o.put("id", id); o.put("ok", err == null); o.put("how", how);
            if (err != null) o.put("error", err);
            act.emit("onSendAudio", o.toString());
        } catch (Exception ignored) { }
    }

    // ── 파일 저장 (내려받기 폴더) : saveBegin → saveChunk… → saveEnd ──
    @JavascriptInterface
    public synchronized boolean saveBegin(String name, String mime) {
        try {
            saveAbort();
            saveName = name;
            if (Build.VERSION.SDK_INT >= 29) {
                ContentValues v = new ContentValues();
                v.put(MediaStore.Downloads.DISPLAY_NAME, name);
                v.put(MediaStore.Downloads.MIME_TYPE, mime == null || mime.isEmpty() ? "application/octet-stream" : mime);
                v.put(MediaStore.Downloads.IS_PENDING, 1);
                saveUri = act.getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                saveOut = act.getContentResolver().openOutputStream(saveUri);
            } else {
                File d = act.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
                saveOut = new FileOutputStream(new File(d, name));
            }
            return saveOut != null;
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "save", t);
            saveAbort();
            return false;
        }
    }

    @JavascriptInterface
    public synchronized boolean saveChunk(String b64) {
        try {
            if (saveOut == null) return false;
            saveOut.write(Base64.decode(b64, Base64.DEFAULT));
            return true;
        } catch (Throwable t) { saveAbort(); return false; }
    }

    @JavascriptInterface
    public synchronized boolean saveEnd() {
        try {
            if (saveOut == null) return false;
            saveOut.close();
            saveOut = null;
            if (saveUri != null && Build.VERSION.SDK_INT >= 29) {
                ContentValues v = new ContentValues();
                v.put(MediaStore.Downloads.IS_PENDING, 0);
                act.getContentResolver().update(saveUri, v, null, null);
            }
            saveUri = null;
            return true;
        } catch (Throwable t) { saveAbort(); return false; }
    }

    private void saveAbort() {
        try { if (saveOut != null) saveOut.close(); } catch (Exception ignored) { }
        saveOut = null;
        if (saveUri != null) try { act.getContentResolver().delete(saveUri, null, null); } catch (Exception ignored) { }
        saveUri = null;
    }

    @JavascriptInterface
    public void keepAwake(boolean on) { act.keepAwake("js", on); }

    @JavascriptInterface
    public void openUrl(final String url) {
        act.ui.post(new Runnable() {
            @Override public void run() {
                try { act.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url))); } catch (Exception ignored) { }
            }
        });
    }
}

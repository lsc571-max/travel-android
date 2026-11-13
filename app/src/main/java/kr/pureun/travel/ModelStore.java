package kr.pureun.travel;

import android.content.SharedPreferences;
import android.os.StatFs;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.RandomAccessFile;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** 폰 안 번역 AI 모델 파일(GGUF) 목록·내려받기·지우기·고르기 */
class ModelStore {
    static class Model {
        String id, name, note, url, file; long approx; boolean custom;
        Model(String id, String name, String note, String url, String file, long approx, boolean custom) {
            this.id = id; this.name = name; this.note = note; this.url = url; this.file = file; this.approx = approx; this.custom = custom;
        }
    }

    static class Job { volatile boolean cancel; volatile long done, total; }

    private final MainActivity act;
    private final SharedPreferences prefs;
    private final File dir;
    private final Map<String, Job> jobs = new HashMap<>();

    ModelStore(MainActivity a) {
        act = a;
        prefs = a.getSharedPreferences("models", 0);
        // 앱 전용 내부 저장소 (번역 엔진이 가장 빠르고 확실하게 읽을 수 있는 곳)
        File d = new File(a.getFilesDir(), "models");
        d.mkdirs();
        dir = d;
    }

    /** 기본 모델 목록: 텐센트 Hy-MT2 1.8B (오픈소스, Apache-2.0, 33개 언어) */
    List<Model> catalog() {
        List<Model> l = new ArrayList<>();
        String base = "https://huggingface.co/tencent/Hy-MT2-1.8B-GGUF/resolve/main/";
        l.add(new Model("hymt2-q4", "Hy-MT2 1.8B · 기본", "추천 · 가볍고 빠름", base + "Hy-MT2-1.8B-Q4_K_M.gguf", "Hy-MT2-1.8B-Q4_K_M.gguf", 1130L * 1000 * 1000, false));
        l.add(new Model("hymt2-q6", "Hy-MT2 1.8B · 정밀", "조금 더 정확 · 조금 느림", base + "Hy-MT2-1.8B-Q6_K.gguf", "Hy-MT2-1.8B-Q6_K.gguf", 1470L * 1000 * 1000, false));
        try {
            JSONArray arr = new JSONArray(prefs.getString("custom", "[]"));
            for (int i = 0; i < arr.length(); i++) {
                JSONObject o = arr.getJSONObject(i);
                l.add(new Model(o.getString("id"), o.getString("name"), "직접 넣은 모델", o.getString("url"), o.getString("file"), 0, true));
            }
        } catch (Exception ignored) { }
        return l;
    }

    Model find(String id) {
        for (Model m : catalog()) if (m.id.equals(id)) return m;
        return null;
    }

    File fileOf(Model m) { return new File(dir, m.file); }

    private File partOf(Model m) { return new File(dir, m.file + ".part"); }

    String selectedId() {
        String sel = prefs.getString("selected", "");
        Model m = find(sel);
        if (m != null && fileOf(m).exists()) return sel;
        for (Model x : catalog()) if (fileOf(x).exists()) return x.id; // 고른 것이 없으면 받아 둔 첫 모델
        return "";
    }

    File selectedFile() {
        Model m = find(selectedId());
        return m == null ? null : fileOf(m);
    }

    void select(String id) {
        prefs.edit().putString("selected", id).apply();
    }

    String listJson() {
        JSONArray arr = new JSONArray();
        String sel = selectedId();
        try {
            for (Model m : catalog()) {
                JSONObject o = new JSONObject();
                File f = fileOf(m), p = partOf(m);
                Job j;
                synchronized (jobs) { j = jobs.get(m.id); }
                o.put("id", m.id); o.put("name", m.name); o.put("note", m.note); o.put("custom", m.custom);
                o.put("approx", m.approx); o.put("url", m.url);
                o.put("selected", m.id.equals(sel));
                if (j != null) { o.put("state", "downloading"); o.put("done", j.done); o.put("total", j.total); }
                else if (f.exists()) { o.put("state", "ready"); o.put("done", f.length()); o.put("total", f.length()); }
                else if (p.exists()) { o.put("state", "partial"); o.put("done", p.length()); o.put("total", m.approx); }
                else { o.put("state", "none"); o.put("done", 0); o.put("total", m.approx); }
                arr.put(o);
            }
        } catch (Exception ignored) { }
        return arr.toString();
    }

    String addCustom(String name, String url) {
        try {
            URL u = new URL(url.trim());
            String path = u.getPath();
            String file = path.substring(path.lastIndexOf('/') + 1);
            if (!file.toLowerCase().endsWith(".gguf")) return "주소가 .gguf 파일로 끝나야 합니다.";
            String id = "custom-" + Integer.toHexString(url.trim().hashCode());
            JSONArray arr = new JSONArray(prefs.getString("custom", "[]"));
            for (int i = 0; i < arr.length(); i++) if (id.equals(arr.getJSONObject(i).getString("id"))) return "";
            JSONObject o = new JSONObject();
            o.put("id", id); o.put("name", name == null || name.trim().isEmpty() ? file : name.trim());
            o.put("url", url.trim()); o.put("file", "c-" + file);
            arr.put(o);
            prefs.edit().putString("custom", arr.toString()).apply();
            return "";
        } catch (Exception e) {
            return "주소를 확인해 주세요.";
        }
    }

    void delete(String id) {
        cancel(id);
        Model m = find(id);
        if (m == null) return;
        fileOf(m).delete();
        partOf(m).delete();
        if (m.custom) {
            try {
                JSONArray arr = new JSONArray(prefs.getString("custom", "[]")), out = new JSONArray();
                for (int i = 0; i < arr.length(); i++) if (!id.equals(arr.getJSONObject(i).getString("id"))) out.put(arr.getJSONObject(i));
                prefs.edit().putString("custom", out.toString()).apply();
            } catch (Exception ignored) { }
        }
        notifyState(id, "none", 0, 0, "");
    }

    void cancel(String id) {
        synchronized (jobs) { Job j = jobs.get(id); if (j != null) j.cancel = true; }
    }

    void cancelAll() {
        synchronized (jobs) { for (Job j : jobs.values()) j.cancel = true; }
    }

    private void notifyState(String id, String state, long done, long total, String msg) {
        try {
            JSONObject o = new JSONObject();
            o.put("id", id); o.put("state", state); o.put("done", done); o.put("total", total); o.put("msg", msg);
            act.emit("onModel", o.toString());
        } catch (Exception ignored) { }
    }

    void download(final String id) {
        final Model m = find(id);
        if (m == null) return;
        final Job job = new Job();
        synchronized (jobs) {
            if (jobs.containsKey(id)) return;
            jobs.put(id, job);
        }
        if (fileOf(m).exists()) {
            synchronized (jobs) { jobs.remove(id); }
            notifyState(id, "ready", fileOf(m).length(), fileOf(m).length(), "");
            return;
        }
        new Thread(new Runnable() {
            @Override public void run() { fetch(m, job); }
        }, "model-download").start();
    }

    private void fetch(Model m, Job job) {
        File part = partOf(m), out = fileOf(m);
        String err = "";
        boolean ok = false;
        HttpURLConnection c = null;
        act.keepAwake("download", true);
        try {
            long have = part.exists() ? part.length() : 0;
            String url = m.url;
            int code = 0;
            for (int hop = 0; hop < 6; hop++) {       // 다른 서버로 넘기는 주소(리다이렉트)를 따라감
                c = (HttpURLConnection) new URL(url).openConnection();
                c.setInstanceFollowRedirects(false);
                c.setConnectTimeout(20000);
                c.setReadTimeout(30000);
                c.setRequestProperty("User-Agent", "TravelInterpreter-Android");
                c.setRequestProperty("Accept-Encoding", "identity");
                if (have > 0) c.setRequestProperty("Range", "bytes=" + have + "-");
                code = c.getResponseCode();
                if (code >= 300 && code < 400 && c.getHeaderField("Location") != null) {
                    url = new URL(new URL(url), c.getHeaderField("Location")).toString();
                    c.disconnect();
                    continue;
                }
                break;
            }
            if (code == 416) { have = 0; part.delete(); throw new Exception("이어받기 실패 · 다시 받기를 눌러 주세요"); }
            if (code != 200 && code != 206) throw new Exception("서버 응답 " + code);
            if (code == 200) have = 0;                  // 서버가 이어받기를 안 받아 줌 → 처음부터
            long len = c.getContentLengthLong();
            long total = len > 0 ? have + len : m.approx;
            StatFs fs = new StatFs(dir.getPath());
            if (len > 0 && fs.getAvailableBytes() < len + 200L * 1024 * 1024)
                throw new Exception("저장 공간이 부족합니다 (" + (len / 1024 / 1024 + 200) + "MB 필요)");
            job.done = have; job.total = total;
            notifyState(m.id, "downloading", have, total, "");
            InputStream in = c.getInputStream();
            RandomAccessFile raf = new RandomAccessFile(part, "rw");
            try {
                raf.setLength(have);
                raf.seek(have);
                byte[] buf = new byte[256 * 1024];
                long lastNote = 0;
                int n;
                while ((n = in.read(buf)) > 0) {
                    if (job.cancel) throw new InterruptedException();
                    raf.write(buf, 0, n);
                    job.done += n;
                    long now = System.currentTimeMillis();
                    if (now - lastNote > 700) { lastNote = now; notifyState(m.id, "downloading", job.done, total, ""); }
                }
            } finally {
                try { raf.close(); } catch (Exception ignored) { }
                try { in.close(); } catch (Exception ignored) { }
            }
            if (len > 0 && job.done < total) throw new Exception("받다가 끊겼습니다 · 다시 누르면 이어서 받습니다");
            // GGUF 파일이 맞는지 확인
            byte[] magic = new byte[4];
            FileInputStream fi = new FileInputStream(part);
            try { if (fi.read(magic) < 4) magic[0] = 0; } finally { fi.close(); }
            if (!(magic[0] == 'G' && magic[1] == 'G' && magic[2] == 'U' && magic[3] == 'F')) {
                part.delete();
                throw new Exception("받은 파일이 AI 모델(GGUF)이 아닙니다 · 주소를 확인해 주세요");
            }
            if (!part.renameTo(out)) throw new Exception("파일을 저장하지 못했습니다");
            ok = true;
        } catch (InterruptedException e) {
            err = "취소했습니다";
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "download", t);
            err = t.getMessage() == null ? t.getClass().getSimpleName() : t.getMessage();
        } finally {
            if (c != null) try { c.disconnect(); } catch (Exception ignored) { }
            synchronized (jobs) { jobs.remove(m.id); }
            act.keepAwake("download", false);
        }
        if (ok) notifyState(m.id, "ready", out.length(), out.length(), "");
        else notifyState(m.id, job.cancel ? "cancelled" : "error", part.exists() ? part.length() : 0, job.total, err);
    }
}

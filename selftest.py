"""
一键自检：改完代码跑一次，13 项全 PASS 才能上线。
用法：python selftest.py
"""
import io, os, re, subprocess, sys, time, tempfile, urllib.request

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HERE = os.path.dirname(os.path.abspath(__file__))

TEST = r"""
<script>
(function(){
  if(location.hash !== '#selftest') return;
  window.alert = function(){};
  var log = [];
  function ok(c, m){ log.push((c ? 'PASS ' : 'FAIL ') + m); }
  setTimeout(function(){
    try{
      data = []; expenses = [];
      try{ DB.clear(); DB.expClear(); }catch(e){}

      document.getElementById('customer').value = '测试客户';
      document.getElementById('owner').value = '测试货主';
      document.getElementById('jian').value = '120';
      document.getElementById('per').value = '50';
      document.getElementById('soil').value = '10';
      document.getElementById('price').value = '1.2';
      document.getElementById('fee').value = '0.05';
      recalc();
      saveRec();
      var r = data[0];
      ok(r.total === 6000, 'T1 总斤数=' + r.total);
      ok(r.soilQty === 600, 'T2 扣土=' + r.soilQty);
      ok(r.net === 5400, 'T3 净重=' + r.net);
      ok(Math.abs(r.amount - 6480) < 0.005, 'T4 总价=' + r.amount);
      ok(Math.abs(r.feeTotal - 270) < 0.005, 'T5 代办=' + r.feeTotal);
      ok(Math.abs(r.actual - 6750) < 0.005, 'T6 实际=' + r.actual);
      ok(r.date === localDate(), 'T7 日期本地=' + r.date);

      renderSum();
      var s1 = (document.getElementById('sumBox').textContent || '').replace(/\s+/g, '');
      ok(s1.indexOf('6,750') >= 0 || s1.indexOf('6750') >= 0, 'T8 汇总含6750');

      document.getElementById('expAmount').value = '300';
      document.getElementById('expPayer').value = '测试';
      saveExp();
      renderSum();
      var s2 = (document.getElementById('sumBox').textContent || '').replace(/\s+/g, '');
      ok(s2.indexOf('300') >= 0, 'T9 汇总费用300');
      ok(s2.indexOf('7,050') >= 0 || s2.indexOf('7050') >= 0, 'T10 总支出7050');

      var acc = [];
      for(var i = 0; i < 100; i++) acc.push({v: 0.1});
      var s = sumFen(acc, function(x){ return x.v; });
      ok(Math.abs(s - 10) < 0.000001, 'T11 100x0.1=' + s);

      var acc2 = [];
      for(var j = 0; j < 3; j++) acc2.push({v: 4231.999999999999});
      var s2b = sumFen(acc2, function(x){ return x.v; });
      ok(Math.abs(s2b - 12696) < 0.01, 'T12 浮点累加=' + s2b);

      ok(round2(1.15 * 3680) === 4232, 'T13 1.15x3680=' + round2(1.15 * 3680));

      var beforeDel = data.length;
      window.confirm = function(){ return true; };
      delRec(data[0].uuid);
      ok(data.length === beforeDel - 1, 'T14 删除后=' + data.length + '条');
      renderSum();
      var s3 = (document.getElementById('sumBox').textContent || '').replace(/\s+/g, '');
      ok(s3.indexOf('6,750') < 0 && s3.indexOf('6750') < 0, 'T15 删除后汇总清零');
    }catch(e){ log.push('ERROR ' + e.message); }
    var d = document.createElement('div');
    d.id = 'selftest-out';
    d.textContent = 'SELFTEST|' + log.join(' ');
    document.body.appendChild(d);
  }, 4500);
})();
</script>
"""

def main():
    src = os.path.join(HERE, "index.html")
    tmp = os.path.join(HERE, "index-selftest.html")
    html = io.open(src, encoding="utf-8").read()
    io.open(tmp, "w", encoding="utf-8", newline="").write(
        html.replace("</body>", TEST + "</body>", 1))

    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8899", "--directory", HERE],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    try:
        out = subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--virtual-time-budget=20000",
             "--dump-dom", "http://localhost:8899/index-selftest.html#selftest"],
            capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=90).stdout
        m = re.search(r'<div id="selftest-out">([^<]*)</div>', out)
        if not m:
            print("✗ 没拿到测试结果（页面可能报错了）")
            return 1
        body = m.group(1).replace("SELFTEST|", "")
        fails = [x for x in re.split(r"(?=PASS |FAIL |ERROR )", body) if x.startswith("FAIL") or x.startswith("ERROR")]
        for part in re.split(r"(?=PASS |FAIL |ERROR )", body):
            if part.strip():
                print(("  ✓ " if part.startswith("PASS") else "  ✗ ") + part[5:].strip())
        print()
        if fails:
            print("✗ 有 %d 项失败，不能上线" % len(fails))
            return 1
        print("✓ 全部通过，可以上线")
        return 0
    finally:
        srv.terminate()
        try: os.remove(tmp)
        except: pass

if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""IndexNow 제출 — 사이트맵 주소 전부를 검색엔진(빙·얀덱스 등)에 «바뀌었어요»로 알린다 (2026-10-20 · DEBUGGER · CTO cto70 AEO ④)

물음: «사이트맵에 있는 주소를 IndexNow 로 한 번에 알렸나».
- 키 = 사이트 뿌리의 `<32자 16진>.txt`(파일 이름 = 안의 글 · 비밀 아님 · IndexNow 가 그 파일을 읽어 주인 확인).
- 🔒기본 = --dry(보내지 않고 셈·앞 몇 줄만 보여 준다) · 실제 제출은 --send 를 붙여야만(제출 손 = CTO).
- 사이트맵 = 기본 라이브 https://hibbangyong.com/sitemap.xml(게시된 주소만 알린다) · --local 이면 이 저장소의 sitemap.xml.
- 한 번에 최대 10,000줄(IndexNow 한도) · 응답 200/202 = 받음 · 그 밖은 그대로 찍는다.
쓰는 법:
  python tools/indexnow.py            # 마른 판(보내기 0)
  python tools/indexnow.py --send     # 제출
"""
import glob
import json
import os
import re
import sys
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

HOST = 'hibbangyong.com'
SITE = 'https://' + HOST
ENDPOINT = 'https://api.indexnow.org/indexnow'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNK = 10000


def key():
    hits = [p for p in glob.glob(os.path.join(ROOT, '*.txt')) if re.fullmatch(r'[0-9a-f]{32}\.txt', os.path.basename(p))]
    if len(hits) != 1:
        raise SystemExit('❌ 뿌리의 키 파일(<32자 16진>.txt)이 %d개(1 아님)' % len(hits))
    k = os.path.basename(hits[0])[:-4]
    if open(hits[0], encoding='utf-8').read().strip() != k:
        raise SystemExit('❌ 키 파일 안의 글 ≠ 파일 이름')
    return k


def urls(local):
    if local:
        xml = open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read()
    else:
        req = urllib.request.Request(SITE + '/sitemap.xml', headers={'User-Agent': 'Mozilla/5.0 (hibbangyong indexnow)'})
        xml = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')
    out = re.findall(r'<loc>([^<]+)</loc>', xml)
    bad = [u for u in out if not u.startswith(SITE + '/')]
    if bad:
        raise SystemExit('❌ 다른 호스트 주소 %d: %s' % (len(bad), bad[:3]))
    return out


def main():
    send, local = '--send' in sys.argv, '--local' in sys.argv
    k = key()
    us = urls(local)
    print('🔑 키 %s(%s/%s.txt) · 주소 %d · 사이트맵 = %s' % (k, SITE, k, len(us), '로컬' if local else '라이브'))
    for u in us[:3]:
        print('   ', u)
    if not send:
        print('🧪 --dry — 보내지 않았다(제출 = --send)')
        return 0
    rc = 0
    for i in range(0, len(us), CHUNK):
        body = json.dumps({'host': HOST, 'key': k, 'keyLocation': '%s/%s.txt' % (SITE, k), 'urlList': us[i:i + CHUNK]}).encode('utf-8')
        req = urllib.request.Request(ENDPOINT, data=body, method='POST', headers={'Content-Type': 'application/json; charset=utf-8'})
        try:
            r = urllib.request.urlopen(req, timeout=60)
            print('📮 %d~%d → %d' % (i + 1, min(i + CHUNK, len(us)), r.status))
            rc |= 0 if r.status in (200, 202) else 1
        except urllib.error.HTTPError as e:
            print('📮 %d~%d → %d %s' % (i + 1, min(i + CHUNK, len(us)), e.code, e.read()[:200]))
            rc = 1
    return rc


if __name__ == '__main__':
    sys.exit(main())

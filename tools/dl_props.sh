#!/usr/bin/env bash
# 从混元 COS 签名直链并行下载 8 个道具 GLB（2026-10-22 批）
set -u
cd "$(dirname "$0")/../assets/models" || exit 1

dl () {
  local name="$1" url="$2"
  curl -sS --noproxy '*' -o "hunyuan-${name}.glb" "$url" \
    && echo "[ok] ${name}: $(stat -c%s "hunyuan-${name}.glb") bytes" \
    || echo "[FAIL] ${name}"
}

dl volcano-active 'https://hunyuan-base-prod-1258344703.cos.ap-guangzhou.myqcloud.com/hunyuan3d/default/ddaa29a7-cddb-11f1-8319-32f6c13eda4a/397f516060b87adc7a722d3215ce87b9.glb?q-sign-algorithm=sha1&q-ak=AKIDRl074nOsGdJ9zjMsCRWP3ShmgS3VtX4S&q-sign-time=1792647963;1824183963&q-key-time=1792647963;1824183963&q-header-list=&q-url-param-list=&q-signature=9698415635d949e15a29fd52ce9c6949d134a53d' &
dl volcano-extinct 'https://hunyuan-base-prod-1258344703.cos.ap-guangzhou.myqcloud.com/hunyuan3d/default/e25f7906-cddc-11f1-8319-32f6c13eda4a/f23163733bf5c1ed820f3c92f74c9010.glb?q-sign-algorithm=sha1&q-ak=AKIDRl074nOsGdJ9zjMsCRWP3ShmgS3VtX4S&q-sign-time=1792647971;1824183971&q-key-time=1792647971;1824183971&q-header-list=&q-url-param-list=&q-signature=558c174d2f1fa35738b08da91189d51b95c480f4' &
dl baobab 'https://hunyuan-base-prod-1258344703.cos.ap-guangzhou.myqcloud.com/hunyuan3d/default/075f2ca7-cddc-11f1-8319-32f6c13eda4a/91e3e3912440b0952fe95b95700bbce1.glb?q-sign-algorithm=sha1&q-ak=AKIDRl074nOsGdJ9zjMsCRWP3ShmgS3VtX4S&q-sign-time=1792648033;1824184033&q-key-time=1792648033;1824184033&q-header-list=&q-url-param-list=&q-signature=3d878873a092126cddee1087945a111018205dba' &
dl throne 'https://hunyuan-base-prod-1258344703.cos.ap-guangzhou.myqcloud.com/hunyuan3d/default/075bb43a-cddc-11f1-8319-32f6c13eda4a/b6cd17e78d193f938813e08af50c4e6e.glb?q-sign-algorithm=sha1&q-ak=AKIDRl074nOsGdJ9zjMsCRWP3ShmgS3VtX4S&q-sign-time=1792648033;1824184033&q-key-time=1792648033;1824184033&q-header-list=&q-url-param-list=&q-signature=ddc57adaf0d832e7db1a02c99f7d26ae9ab9b374' &
dl streetlamp 'https://hunyuan-base-prod-1258344703.cos.ap-guangzhou.myqcloud.com/hunyuan3d/default/fa51e7fa-cddc-11f1-8319-32f6c13eda4a/6708d041a7b0ec7b9fff91834df38c23.glb?q-sign-algorithm=sha1&q-ak=AKIDRl074nOsGdJ9zjMsCRWP3ShmgS3VtX4S&q-sign-time=1792648012;1824184012&q-key-time=1792648012;1824184012&q-header-list=&q-url-param-list=&q-signature=dc979f61009d6f894465506e58114e7e6a45c600' &
dl globe 'https://hunyuan-base-prod-1258344703.cos.ap-guangzhou.myqcloud.com/hunyuan3d/default/3d12c8bf-cddc-11f1-8319-32f6c13eda4a/b5e7335e538ef3901b1cb10fd3905558.glb?q-sign-algorithm=sha1&q-ak=AKIDRl074nOsGdJ9zjMsCRWP3ShmgS3VtX4S&q-sign-time=1792648123;1824184123&q-key-time=1792648123;1824184123&q-header-list=&q-url-param-list=&q-signature=6be50e426b199aae7c806c24ad28dd617a951e9c' &
dl giant-book 'https://hunyuan-base-prod-1258344703.cos.ap-guangzhou.myqcloud.com/hunyuan3d/default/3d15b4dc-cddc-11f1-8319-32f6c13eda4a/6a04bd2a66d117ed048bd8a65ee32b74.glb?q-sign-algorithm=sha1&q-ak=AKIDRl074nOsGdJ9zjMsCRWP3ShmgS3VtX4S&q-sign-time=1792648123;1824184123&q-key-time=1792648123;1824184123&q-header-list=&q-url-param-list=&q-signature=45131943e18a53d085066e3b255983182fc06c49' &
dl plane-wreck 'https://hunyuan-base-prod-1258344703.cos.ap-guangzhou.myqcloud.com/hunyuan3d/default/28ce90fe-cddc-11f1-8319-32f6c13eda4a/6a0919d5f3426d5f68c3d20513c44fb1.glb?q-sign-algorithm=sha1&q-ak=AKIDRl074nOsGdJ9zjMsCRWP3ShmgS3VtX4S&q-sign-time=1792648089;1824184089&q-key-time=1792648089;1824184089&q-header-list=&q-url-param-list=&q-signature=b460f297112d0e573352d1bc51697be2788ac3c6' &
wait
echo "=== all done ==="
ls -la hunyuan-volcano-active.glb hunyuan-volcano-extinct.glb hunyuan-baobab.glb hunyuan-throne.glb hunyuan-streetlamp.glb hunyuan-globe.glb hunyuan-giant-book.glb hunyuan-plane-wreck.glb

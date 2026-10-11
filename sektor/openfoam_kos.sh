#!/bin/sh
# OpenFOAM v2506 (ESI/OpenCFD resmi Docker imajı) ile laminer boru: ağ → kontrol → çözüm. 2 çekirdekte ~3 dakika.
cd "$(dirname "$0")" || exit 1
docker run --rm --cpus 2 -u "$(id -u):$(id -g)" -v "$PWD/openfoam:/case" opencfd/openfoam-default:2506 \
  bash -c "cd /case/boru_laminer && sh ./Allrun"

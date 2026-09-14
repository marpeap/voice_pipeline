#!/usr/bin/env bash
# Banc L0 — tenue en charge. Conçu pour tenir dans UNE session SSH de moins de 110 s,
# parce que marpeap-series se rendort dès que la session se ferme (voir docs/09-L0-MESURES.md).
cd ~/bancs/l0-nemo/NeMo-Speech.cpp
M=$HOME/bancs/l0-nemo/modele/nemotron-3.5-asr-streaming-0.6b.q8_0.gguf
F=$HOME/bancs/l0-corpus/017_tel.wav
duree=$(~/miniforge3/bin/python -c "import wave; w = wave.open('$F'); print(round(w.getnframes()/w.getframerate(), 2))")
echo "reference : ${duree} s d audio, modele 742 Mo"
for N in 1 2 4; do
  avant=$(free -m | awk '/^Mem/{print $7}')
  start=$(date +%s.%N)
  for i in $(seq $N); do ./build/bin/nemo-speech transcribe --quiet --model "$M" "$F" >/dev/null 2>&1 & done
  sleep 3
  pendant=$(free -m | awk '/^Mem/{print $7}')
  wait
  end=$(date +%s.%N)
  ~/miniforge3/bin/python -c "
mur = $end - $start
n, d, ram = $N, $duree, $avant - $pendant
print('  %d appel(s) : %5.1f s mur | %5.2f x la duree audio | RAM %4d Mo' % (n, mur, mur/d, ram))"
done
echo CHARGE_OK

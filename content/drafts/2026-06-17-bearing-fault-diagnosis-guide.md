# Bearing Fault Diagnosis Guide

## Target query
- bearing fault diagnosis
- bearing fault diagnosis using vibration analysis
- bearing fault diagnosis deep learning

## Reader problem
베어링 고장 진단을 처음 설계하거나, FFT 기반 전통 기법과 딥러닝 기반 접근 중 무엇을 먼저 도입해야 할지 판단하고 싶은 독자를 위한 글.

## Recommended structure
1. What bearing fault diagnosis is actually trying to detect
2. Sensor choices: vibration, AE, temperature, current
3. Signal pipeline: FFT, envelope analysis, spectrogram, entropy, learned features
4. Model families: classical ML vs CNN vs Transformer vs transfer learning
5. What changes under variable speed and cross-machine conditions
6. Benchmark traps: why high accuracy is not enough
7. Deployment checklist for rolling stock / rotating equipment
8. Best papers and MALT deep dives to read next

## Existing MALT posts to link
- /posts/2026-02-21-railway-phm-fft-1dcnn.html
- /posts/2026-02-19-bearing-ae-sensor.html
- /posts/2026-06-16-251206837v1-neural-factorization-based-bearing-fault-diagnosis.html
- /posts/2026-06-16-241102718v1-llm-based-framework-for-bearing-fault-diagnosis.html

## Conversion goal
- Capture broad industrial search traffic
- Route readers into daily bearing paper analysis posts

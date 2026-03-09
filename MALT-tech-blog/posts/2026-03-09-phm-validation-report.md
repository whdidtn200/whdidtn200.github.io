---
title: "[Validation Report] IEEE PHM 2012 베어링 데이터셋을 활용한 VAE 모델 검증 및 성능 분석"
date: 2026-03-09
categories: [PHM, Anomaly Detection]
tags: [VAE, IEEE-PHM-2012, Model-Validation, Confusion-Matrix]
---

# IEEE PHM 2012 베어링 데이터셋을 활용한 VAE 모델 검증 및 성능 분석

## 1. 개요
본 리포트는 IEEE PHM 2012 베어링 데이터셋을 활용하여 MALT 시스템의 VAE 기반 이상 탐지 성능을 정밀 검증한 결과를 담고 있습니다.

## 2. 검증 결과
| Metric | Value |
| :--- | :--- |
| **ROC AUC** | 0.7748 |
| **Average Precision (AP)** | 0.6358 |
| **Optimal Threshold** | 2.6279 |

## 3. 오차행렬
- 정탐(TP): 689 / 오탐(FP): 174 / 미탐(FN): 821 / 진음(TN): 5850

# 미리와봄 (AI-Gym) 작업 로드맵 & 체크리스트

> **목표**: 시니어(65+) 친화 Unity 6 URP WebGL 가상 헬스장 + AI 트레이너 사전 체험 플랫폼 완성  
> **현재 빌드 씬 구성**: `intro.unity` → `AIGym.unity` ↔ `GXStudio.unity`

---

## ✅ 완료된 주요 작업 (2026-11-24 ~ 11-25)

- [x] **GX룸 (`GXStudio.unity`) 리모델링**: 30평 운동 바닥, EGOJIN 파스텔 TPE 요가매트 21개, 모듈러 덤벨/케틀벨 2단 랙, 무대·대형 스크린·모니터 스피커 정렬
- [x] **헬스장 (`AIGym.unity`) 구조 최적화**: 218.2평 리사이즈, 외곽 바닥 폴리곤 경량화, 2단계 온보딩 팝업(`WelcomCanva`) 제작
- [x] **프로 AI 트레이너 아바타 제작 (`AI_Trainer_Pro`)**: 공식 65본 Mixamo 리그 + 30관절 손가락 웨이트 복구 + 타이즈/헤드셋/스마트워치 PBR 텍스처 (`2.53 MB`)
- [x] **운동 기구 애니메이션 경량화 & 제작**:
  - `LatPulldown_ani.fbx` (`133.6 MB` → `9.21 MB`)
  - `LegExtension_ani.fbx` (`2.84 MB`)
  - `ChestPress_ani_done.fbx` (`5.19 MB`, 72프레임 무한 루프, 10개 손가락 그립 밀착)
- [x] **블렌더/FBX 폴더 정리 (`_blender/`)**: `Blend/`, `FBX/`, `Scripts/`, `Archive/` 분리 및 GitHub 100MB 초과 차단 방지
- [x] **Unity 6 URP & WebGL 전체 최적화**: 미사용 2K 텍스처 `114 MB` 제거, 텍스처 94개 1024px+Crunch 압축, FBX 18개 Medium 압축, URP 불필요 패스 해제
- [x] **Gemini API 최신화**: `gemini-4-hydrogen` (메인) + `gemini-3.5-flash-lite` (폴백) + `gemini-3.8-flash-tts` Interactions REST 파싱 수정 + 로컬 API 키 보안 적용

---

## 🎯 오늘 오전 10시 핵심 작업

### 1. 헬스장 (`AIGym.unity`) 리모델링 마무리
- [ ] 체스트프레스(`ChestPress_ani_done.fbx`) 등 운동 기구 최종 배치 및 조명/동선 정리
- [ ] 입장 설문(`DoorSurvey.cs`) → 불편 부위 선택 후 **"체험 시작하기"** 클릭 시 추천 기구(`RecommendSpots`) 앞 이동/안내 연결

### 2. GX룸 (`GXStudio.unity`) AI 트레이너 & 맨몸운동 구축
- [ ] GX룸 무대 위 `AI_Trainer_Pro.fbx` 배치
- [ ] GX룸에 `GeminiClient` (`gemini-4-hydrogen`) + `TrainerVoice` (`gemini-3.8-flash-tts`) 실시간 코칭/자막 연동
- [ ] 블렌더(`_blender/Blend/AI_Trainer_Pro.blend`)로 시니어 친화적 맨몸운동 애니메이션 제작 & 경량 FBX 임포트
  - [ ] 예: 하프 스쿼트 / 어깨·팔 스트레칭 / 제자리 무릎 들기 등 2~3종 루프

---

## 🔗 1순위: 전체 체험 동선 완성 (필수 기능)

- [ ] **기구 접근 시 AI 트레이너 인사·시범 재연결 (`GymUI` → `TrainerAppear` / `ExerciseStation`)**
  - 교체된 새 `LatPulldown_ani`, `ChestPress_ani_done`, `LegExtension_ani`에 `machine`, `seatPoint`, `facing`, `trainer` 참조 연결
- [ ] **`AIGym.unity` ↔ `GXStudio.unity` 왕복 씬 이동 점검 (`SceneLoader` / `DoorTrigger`)**
  - 헬스장 ↔ GX룸 자연스러운 왕복 이동 및 스폰 위치 확인
- [ ] **체험 종료 요약 카드 (`SummaryCard.cs`) 점검**
  - 기구·GX 체험 기록 누적 및 퇴장 시 *"오늘 체험 기록 — 현장 선생님께 보여주세요"* 카드 정상 표시 확인

---

## ✨ 2순위: 시니어(65+) 맞춤 완성도 디테일

- [ ] **GX룸 무대 대형 스크린 (`ScreenDisplay`) 콘텐츠 적용**
  - 현재 맨몸운동 이름, 호흡 가이드, 횟수/타이머 등 화면 표시
- [ ] **헬스장 기구별 큰 한글 안내 표지판 & 바닥 동선 가이드**
  - 어르신이 직관적으로 찾을 수 있게 기구 옆 큰 글씨 이름표 배치 (예: `체스트 프레스 · 가슴/팔 근력`)
- [ ] **시니어 UI 가독성 통일 & 사운드 밸런스**
  - `intro` → `WelcomCanva` → `TrainerSpeechCanvas` → `TrainerChat` → `SummaryCard` 글자 크기·고대비 여백 통일
  - GX룸 잔잔한 배경음 + AI 트레이너 음성 볼륨 균형 및 음소거 버튼 점검

---

## 🚀 3순위: WebGL 실전 빌드 & 최종 완주 테스트

- [ ] **WebGL 빌드 생성 및 최종 용량 확인**
- [ ] **브라우저 실전 검증 (처음부터 끝까지 1회 완주)**
  - [ ] `intro.unity` → `AIGym.unity` (온보딩 설문 → 기구 체험) → `GXStudio.unity` (AI 맨몸운동) → `SummaryCard`
  - [ ] 브라우저 오디오 정책(첫 클릭 이후 `TrainerVoice` TTS 재생) 정상 작동 확인
  - [ ] WebGL 환경에서 `GeminiClient` API 호출 및 CORS 오류 없음 확인

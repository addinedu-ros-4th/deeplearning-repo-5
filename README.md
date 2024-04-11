# 딥러닝 기반의 실시간 수어 번역 화상 통신 시스템
<div align="center">
  
![스크린샷 2024-04-05 224224](https://github.com/AUTO-KKYU/PythonTCP_IP_Socket_Communication/assets/118419026/8b1319ae-25a8-454b-8eca-042dcdacbcb7)
<h3 align="middle">AI 실시간 화상 수어 번역 서비스</h3>

<div align="left">

## 목차
  * [1. 🤖프로젝트 소개](#1-프로젝트-소개)
  * [2. 👨‍👨‍👦‍👦팀원 소개](#2-팀원-소개)
  * [3. 📋시스템 설계](#3-시스템-설계)
    + [3-1. 기술 스택](#3-1-기술-스택)
    + [3-2. 기능리스트](#3-2-기능리스트)
    + [3-3. 전체 알고리즘 과정 흐름도](#3-3-전체-알고리즘-과정-흐름도)
    + [3-4. 실시간 영상 처리 프로세스](#3-4-실시간-영상-처리-프로세스)
      - [3-4-1. Camera Manager](#3-4-1-camera-manager)
      - [3-4-2. Audio Manager](#3-4-2-audio-manager)
      - [3-4-3. Auto Correct](#3-4-3-auto-correct)
    + [3-5. 수어 인식 모델 딥러닝 학습 흐름도](#3-5-수어-인식-모델-딥러닝-학습-흐름도)
    + [3-6. 네트워크 구성도](#3-6-네트워크-구성도)
  * [4. 🎐GUI](#4-🎐gui)
    + [4-1. SERVER GUI](#4-1-server-gui)
    + [4-2. CLIENT GUI](#4-2-client-gui)
  * [5. 📸구현 영상](#5-📸구현-영상)
  * [6. 📖회고](#6-📖회고)

- 워크 스페이스 : https://zrr.kr/M2br
- 발표자료 : https://zrr.kr/QMWA
  
## 1. 🤖프로젝트 소개
- 🤞 이것은 손짓이 아니라, THIS IS COMMUNICATION
- 청인과 농인간 원활한 의사소통을 위한 AI 실시간 수어 번역 서비스
- 양방향 소통 개선을 위해 서로가 표현하는 언어에 대해 이해하고 파악할 수 있도록 하나의 아이디어를 제시
- 프로젝트 기간 : 2024.03.14 ~ 2024.04.11 (중 10일)
<div align="left">

![스크린샷 2024-04-10 214946](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/bd8c837c-505d-40ca-9f20-7f98703d2a36)

## 2. 👨‍👨‍👦‍👦팀원 소개

| **윤현준** | **김동규** | **송용탁** | **유윤하** | **이재혁** |
| :------: |  :------: | :------: | :------: | :------: |
| [![download_image_1712199366284](https://github.com/AUTO-KKYU/PythonTCP_IP_Socket_Communication/assets/118419026/870dcf89-bf3f-4190-9423-c3bf4e21783f) <br/> @YoonHJ97](https://github.com/YoonHJ97) | [![download_image_1712199283923-Photoroom png-Photoroom](https://github.com/AUTO-KKYU/PythonTCP_IP_Socket_Communication/assets/118419026/e0bb91be-be3a-4eee-922c-473c43958cf4) <br/> @AUTO-KKYU](https://github.com/AUTO-KKYU) | [![download_image_1712200407678](https://github.com/AUTO-KKYU/PythonTCP_IP_Socket_Communication/assets/118419026/3e44828c-a5aa-4940-8874-27a27e030a61) <br/> @okotak99](https://github.com/okotak99) | [![download_image_1712200424618](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/3b0cd60d-4903-4dae-b183-828ffadd352d) <br/> @yoonha-ryu-96](https://github.com/yoonha-ryu-96) | [![image-Photoroom png-Photoroom](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/bd36e538-bdb0-4716-ac97-e16e7c5f54fa) <br/> @RedStones-112](https://github.com/RedStones-112)

|팀원|역할| 
|:---:|:---|
|팀장 윤현준|- 프로젝트 총괄(팀장) <br>- 지문자 인식 Server 연동 <br>- 한글 키보드 알고리즘 구현 <br>- 자동생성기 및 STT,TTS,지문자 출력 및 속도 조절 기능 개발 <br>- DataSet 수집|
|김동규|- Socket 통신 기반 영상통화 시스템 구현<br> - PyQt6 기반 영상통화 GUI 개발(서버 및 클라이언트) <br>- 클라이언트 접속 이력 DB 관리 <br> - 프로젝트 산출물 정리 총괄|
|송용탁|- Socket 통신 기반 영상통화 시스템 구현<br> - PyQt6 기반 영상통화 GUI 개발(서버 및 클라이언트) <br>- 통신부 코드 최적화 <br> - 프로젝트 산출물 정리|
|유윤하| - 비동기 프로세스 및 Thread 관리 <br> - 지문자 인식, Server 연동 PM <br> - 수어인식 모델(LSTM) 학습<br> - Data 전처리  <br>|
|이재혁|- MediaPipe, 딥러닝 인식모델 학습 및 검증 <br>- 지문자 인식 Server 연동 <br>- 프로그램 코드 최적화 및 구성도 작성|

<br>

## 3. 📋시스템 설계

### 3-1. 기술 스택

||| 
|:---:|:---|
|개발환경|<img src="https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=Ubuntu&logoColor=white"> <img src="https://img.shields.io/badge/VISUAL STUDIO CODE-007ACC?style=for-the-badge&logo=VisualStudioCode&logoColor=white"> <img src="https://img.shields.io/badge/Google%20Colab-F9AB00?style=for-the-badge&logo=Google%20Colab&logoColor=orange">|
|기술|<img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54"> <img src="https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white"> <img src = "https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white"> <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white"> <img src="https://img.shields.io/badge/Qt-5C3EE8?style=for-the-badge&logo=Qt&logoColor=#41CD52"> <img src="https://img.shields.io/badge/mysql-4479A1.svg?style=for-the-badge&logo=mysql&logoColor=white"> <img src = "https://img.shields.io/badge/Keras-%23D00000.svg?style=for-the-badge&logo=Keras&logoColor=white"> <img src ="https://img.shields.io/badge/TensorFlow-%23FF6F00.svg?style=for-the-badge&logo=TensorFlow&logoColor=white"> |
|COMMUNICATION|<img src="https://img.shields.io/badge/Slack-4A154B?style=for-the-badge&logo=Slack&logoColor=white"> <img src="https://img.shields.io/badge/notion-000000?style=for-the-badge&logo=notion&logoColor=white"> <img src="https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white">|

### 3-2. 기능리스트
![스크린샷 2024-04-10 220346](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/d9df4b2c-3f30-4d3f-ab4b-69a5b1c2e826)

### 3-3. 전체 알고리즘 과정 흐름도
![DL_system-페이지-15 drawio (3)](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/80ef5b1c-5e7e-4f55-86df-f8e7e19c2767)

### 3-4. 실시간 영상 처리 프로세스
#### 3-4-1. Camera Manager
![DL_system-페이지-11 drawio](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/c3d7e58a-c771-4ab8-99ff-aa51d3d905b7)

#### 3-4-2. Audio Manager
![DL_system-페이지-11 drawio (1)](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/f773d99a-c9ed-4255-bbb9-6283e7622f10)

#### 3-4-3. Auto Correct
![DL_system-페이지-11 drawio (2)](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/094bca5c-1fe3-4f78-bda5-396e9feaa91f)

### 3-5. 수어 인식 모델 딥러닝 학습 흐름도
![DL_system-페이지-14 drawio](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/5ace9f8e-ff35-4642-8553-cd5e7481ce33)

### 3-6. 네트워크 구성도
![Untitled (8)](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/b12e6312-3622-4c96-93cc-3b1b41479414)

<br>

## 4. 🎐GUI
### 4-1. SERVER GUI

![스크린샷 2024-04-05 223343](https://github.com/AUTO-KKYU/PythonTCP_IP_Socket_Communication/assets/118419026/a38462e3-1bce-407c-8e19-bb115368d0dc)

- Start Button : 서버 활성화
- Stop Button : 서버 비활성화
- Search Button : 각 콤보박스에 대한 쿼리 실행

### 4-2. CLIENT GUI 
- **Login GUI**
  - 사용자명을 입력하고 로그인 버튼 클릭 시, 클라이언트 창으로 넘어갑니다
  - 단, 서버가 활성화 된 상태에서만 서버로 접속가능합니다
![스크린샷 2024-04-05 225013](https://github.com/AUTO-KKYU/PythonTCP_IP_Socket_Communication/assets/118419026/82969ddf-e2d6-43d3-930c-739cfcb89266)
- **client GUI**
  - 해당 인터페이스에서 현재 서버에 접속중인 사용자를 확인할 수 있습니다
  - 현재 접속중인 클라이언트 테이블에서 연결하고 싶은 특정 대상에 대해 Connect버튼을 클릭 하게 되면, 해당 사용자의 ip와 port를 불러옵니다
  - 불러온 정보를 확인하고 Call버튼을 클릭 하게 되면 화상채팅 창으로 넘어갑니다

      ※ **단, 상대방도 동일한 조건으로 실행해줘야 합니다**
![Screenshot from 2024-04-05 15-03-31](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/61307553/5f1f1308-ee7e-465a-a465-c278bdda54ed)

- **Facechat GUI**
  - 화상채팅 창에서 화면 공유 버튼 클릭 시, 나의 화면을 상대방에게 보냅니다
  - 상대방도 동일한 조건으로 실행 시, 자신의 화면을 상대방에게 공유합니다
  - **세부기능**
    - 수어 모드 : 손동작 인식을 활성화 시켜 지문자 출력 모드 ON, 한번 더 클릭 시, OFF 됩니다
    - STT : 음성을 인식하여 단어 혹은 문장을 출력합니다
    - TTS : 수신받은 단어 혹은 문장을 출력합니다
    - Filter : 화면에 필터 효과를 줄 수 있습니다
    - Guide : 지문자 사전을 보여줍니다
    - reset Button : 텍스트 초기화
    - 연결 종료 : 상대방과의 연결을 끊습니다

![Screenshot from 2024-04-05 14-50-53](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/61307553/42cd4223-316c-4194-8e84-813ea1ef1411)
![스크린샷 2024-04-05 211439](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/3dfedd46-2293-4bf6-bdc2-e45896224a6a)

<br>

## 5. 📸구현 영상
[![Video](https://img.youtube.com/vi/OCahwtk-_Q0/sddefault.jpg)](https://www.youtube.com/watch?v=OCahwtk-_Q0&t=21s)


<br>

## 6. 📖회고







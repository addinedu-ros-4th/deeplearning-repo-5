# 딥러닝 기반의 실시간 수어 번역 화상 통신 시스템
<div align="center">
  
![Screenshot from 2024-04-04 14-16-34](https://github.com/AUTO-KKYU/TEST/assets/118419026/cac31317-e82b-4bce-91b0-f781a907524c)
<h3 align="middle">AI 실시간 화상 수어 번역 서비스</h3>

<div align="left">

## 목차
  * [1. 🤖프로젝트 소개](#1-프로젝트-소개)
  * [2. 👨‍👨‍👦‍👦팀원 소개](#2-팀원-소개)
  * [3. 📋시스템 설계](#3-시스템-설계)
    + [3-1. 기술 스택](#3-1-기술-스택)
    + [3-2. 주요 기술](#3-2-주요-기술)
    + [3-3. 기능리스트](#3-3-기능리스트)
    + [3-4. 전체 알고리즘 과정 흐름도](#3-4-전체-알고리즘-과정-흐름도)
    + [3-5. 수어 인식 모델 딥러닝 학습 흐름도](#3-5-수어-인식-모델-딥러닝-학습-흐름도)
    + [3-6. 수어 검출 다이어그램](#3-6-수어-검출-다이어그램)
    + [3-7. TCP/IP 소켓 통신 시나리오](#3-7-tcpip-소켓-통신-시나리오)
  * [🎐4. GUI](#4-gui)
    + [4-1. SERVER GUI](#4-1-server-gui)
    + [4-2. CLIENT GUI](#4-2-client-gui)
  * [5. 📸구현 영상](#5-구현-영상)
  * [6. 📖회고](#6-회고)


- 워크 스페이스 : https://zrr.kr/M2br
  
## 1. 🤖프로젝트 소개
- 🤞 이것은 손짓이 아니라, THIS IS COMMUNICATION
- 청인과 농인간 원활한 의사소통을 위한 AI 실시간 수어 번역 서비스
- 양방향 소통 개선을 위해 서로가 표현하는 언어에 대해 이해하고 파악할 수 있도록 하나의 아이디어를 제시
- 프로젝트 기간 : 2024.03.14 ~ 2023.04.11 (중 10일)
![Screenshot from 2024-04-04 15-07-27](https://github.com/AUTO-KKYU/TEST/assets/118419026/51121f1c-0e5d-4ae5-a587-6f0ba8735240)

## 2. 👨‍👨‍👦‍👦팀원 소개

| **윤현준** | **김동규** | **송용탁** | **유윤하** | **이재혁** |
| :------: |  :------: | :------: | :------: | :------: |
| [![download_image_1712199366284](https://github.com/AUTO-KKYU/TEST/assets/118419026/d2fad8ee-46ac-49e1-b011-ccf0a9914f98) <br/> @YoonHJ97](https://github.com/YoonHJ97) | [![스크린샷 2024-04-04 194216](https://github.com/AUTO-KKYU/TEST/assets/118419026/1ee1f96a-19b9-4088-87a7-522d418a6320) <br/> @AUTO-KKYU](https://github.com/AUTO-KKYU) | [![download_image_1712198928013](https://github.com/AUTO-KKYU/TEST/assets/118419026/11f16474-eae6-405f-82e6-cf8bafd7fbcf) <br/> @okotak99](https://github.com/okotak99) | [![download_image_1712200424618 (1)](https://github.com/AUTO-KKYU/TEST/assets/118419026/8b2ff8ff-01e9-4af8-b18e-179b73b963c9) <br/> @yoonha-ryu-96](https://github.com/yoonha-ryu-96) | [![image-Photoroom png-Photoroom](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/bd36e538-bdb0-4716-ac97-e16e7c5f54fa) <br/> @RedStones-112](https://github.com/RedStones-112)

|팀원|역할| 
|:---:|:---|
|팀장 윤현준|- 프로젝트 팀장 <br> - Mediapipe <br>- PyQt <br>- 딥러닝 수어인식 모델 학습 <br>- 자동생성기 및 STT,TTS,지문자 출력 및 속도 조절 기능 개발  |
|김동규|- 파이썬 소켓 통신 기반 통신 시스템 구현<br> - PyQt6 기반 서버 및 각종 클라이언트 GUI 개발 <br>- 클라이언트 접속 이력 DB 관리 <br> - 프로젝트 진행 사항 및 협업을 위한 자료 정리 총괄|
|송용탁|- 파이썬 소켓 통신 기반 통신 시스템 구현<br> - PyQt6 기반 서버 및 각종 클라이언트 GUI 개발 <br> - 프로젝트 진행 사항 및 협업을 위한 자료 정리 <br> - 통신관련 버그 해결|
|유윤하| - 비동기 프로세스 처리<br> - Thread 관리<br> - 개발 계획 총괄<br> - 수어인식 모델(LSTM) 학습<br> - 딥러닝 수어인식 모델 학습 <br>|
|이재혁|- MediaPipe, 인식모델 파트 총괄<br> - 딥러닝 수어인식 모델 학습<br> - 통신, DeepLearning 파트 통합<br> - 프로그램 조율 |

<br>

## 3. 📋시스템 설계

### 3-1. 기술 스택

||| 
|:---:|:---|
|개발환경|<img src="https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=Ubuntu&logoColor=white"> <img src="https://img.shields.io/badge/VISUAL STUDIO CODE-007ACC?style=for-the-badge&logo=VisualStudioCode&logoColor=white"> <img src="https://img.shields.io/badge/Google%20Colab-F9AB00?style=for-the-badge&logo=Google%20Colab&logoColor=orange">|
|기술|<img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54"> <img src="https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white"> <img src = "https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white"> <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white"> <img src="https://img.shields.io/badge/Qt-5C3EE8?style=for-the-badge&logo=Qt&logoColor=#41CD52"> <img src="https://img.shields.io/badge/mysql-4479A1.svg?style=for-the-badge&logo=mysql&logoColor=white"> <img src = "https://img.shields.io/badge/Keras-%23D00000.svg?style=for-the-badge&logo=Keras&logoColor=white"> <img src ="https://img.shields.io/badge/TensorFlow-%23FF6F00.svg?style=for-the-badge&logo=TensorFlow&logoColor=white"> |
|COMMUNICATION|<img src="https://img.shields.io/badge/Slack-4A154B?style=for-the-badge&logo=Slack&logoColor=white"> <img src="https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white"> <img src="https://img.shields.io/badge/notion-000000?style=for-the-badge&logo=notion&logoColor=white"> <img src="https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white">|

### 3-2. 주요 기술
![스크린샷 2024-04-04 193538](https://github.com/AUTO-KKYU/TEST/assets/118419026/2d34c3f1-aaf6-49f7-9484-8eaec2fbbd53)

<br>

### 3-3. 기능리스트
![Screenshot from 2024-04-05 15-00-15](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/61307553/020585cf-1c59-4dbe-8508-4e0e64971c63)


### 3-4. 전체 알고리즘 과정 흐름도
![DL_system-Page-7 drawio](https://github.com/AUTO-KKYU/TEST/assets/118419026/e5f3254e-e4eb-422a-9b40-5744ddfbe1e9)

### 3-5. 수어 인식 모델 딥러닝 학습 흐름도
![DL_system-Page-5 drawio](https://github.com/AUTO-KKYU/TEST/assets/118419026/884ed9af-47c5-4820-a261-23a0287fe5c3)

### 3-6. 수어 검출 다이어그램
![DL_system-Page-2 drawio](https://github.com/AUTO-KKYU/TEST/assets/118419026/e06b22bf-e1ad-4109-a435-99fe669942b3)


### 3-7. TCP/IP 소켓 통신 시나리오 
![Untitled](https://github.com/AUTO-KKYU/TEST/assets/118419026/2c0ab405-f856-4f85-a3cf-e484ab353f68)

## 4. 🎐GUI
### 4-1. SERVER GUI
![스크린샷 2024-04-04 210406](https://github.com/AUTO-KKYU/TEST/assets/118419026/dd7d0872-4a83-4eb5-8a05-d11c214d3807)

- Start Button : 서버 활성화
- Stop Button : 서버 비활성화
- Search Button : 각 콤보박스에 대한 쿼리 실행

### 4-2. CLIENT GUI 
- Login GUI
  - 사용자명을 입력하고 로그인 버튼 클릭 시, 클라이언트 창으로 넘어갑니다
  - 단, 서버가 활성화 된 상태에서만 서버로 접속가능합니다
![스크린샷 2024-04-04 213131](https://github.com/AUTO-KKYU/TEST/assets/118419026/bde7b91f-a674-464a-a89b-e0d215cca17c)

- client GUI
  - 해당 인터페이스에서 현재 서버에 접속중인 사용자를 확인할 수 있습니다
  - 현재 접속중인 클라이언트 테이블에서 연결하고 싶은 특정 대상에 대해 Connect버튼을 클릭 하게 되면, 해당 사용자의 ip와 port를 불러옵니다
  - 불러온 정보를 확인하고 Call버튼을 클릭 하게 되면 화상채팅 창으로 넘어갑니다

      ※ **단, 상대방도 동일한 조건으로 실행해줘야 합니다**
![Screenshot from 2024-04-05 15-03-31](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/61307553/5f1f1308-ee7e-465a-a465-c278bdda54ed)

- Facechat GUI
  - 화상채팅 창에서 화면 공유 버튼 클릭 시, 나의 화면을 상대방에게 보냅니다
    - 상대방도 동일한 조건으로 실행 시, 자신의 화면을 상대방에게 공유합니다
  - 수어 모드 : 손동작 인식을 활성화 시켜 지문자 출력 모드 ON, 한번 더 클릭 시, OFF 됩니다
  - STT : 음성을 인식하여 단어 혹은 문장을 출력합니다
  - TTS : 수신받은 단어 혹은 문장을 출력합니다
  - Filter : 화면에 필터 효과를 줄 수 있습니다
  - Guide : 지문자 사전을 보여줍니다
  - 연결 종료 : 상대방과의 연결을 끊습니다

![Screenshot from 2024-04-05 15-03-31](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/61307553/5f1f1308-ee7e-465a-a465-c278bdda54ed)
![Screenshot from 2024-04-05 14-50-53](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/61307553/42cd4223-316c-4194-8e84-813ea1ef1411)

<br>

## 5. 📸구현 영상


<br>

## 6. 📖회고







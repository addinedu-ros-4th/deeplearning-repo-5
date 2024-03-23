# deeplearning-repo-5
딥러닝 프로젝트 5조. 실시간 수어 통역 화상 통신 시스템 : 딥러닝 기술을 활용한 수어-음성 변환 플랫폼

## 활용 목적
- 대화는 때로는 말이 아닌,제스처 혹은 몸짓을 통해 의사전달을 할 때가 있다. 특히 농인과 대화하는 경우에 수어를 잘 알지 못하면 문맥을 파악하지 못하는 경우가 있다. 이러한 양방향 소통 개선을 위해 서로가 표현하는 언어에 대해
  잘 이해하고 문맥을 파악할 수 있도록 하나의 아이디어를 제시한다.
- 농인과 청인 사이에 소통할 때는 둘 다 수어를 하거나 문자로 소통하는 방법이 많이 쓰일 것이다. 하지만 "대화"를 하는데 있어 농인은 수어를 사용하고 청인은 말을 하는게 더욱 이상적일 것이라고 생각했다.
그래서 실시간으로 수어를 문자화하고 음성을 문자화하여 소통하면 대화에 가까워 질 것이라고 생각하여 이런 시스템을 구상했다.

### 제스처(손동작) 인식 기능 개선
- 한가지 음운을 1초이상 하고있을경우 화면 상에 띄우기 + GUI label : text화 두 개 모두 적용 
- 특수문자 : space(띄어쓰기)와 clear(새로고침), delete(지우기) : 기존 수화와 손동작이 겹치지 않게
- 한글 자연어처리 : 한국어 텍스트 자음/모음 적절하게 분리 및 결합

![Screenshot from 2024-03-20 13-38-51](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/8fc246e0-b344-4a6e-b9b7-cc85ba9a2b69)

### 시나리오

![DL_system-Page-2 drawio (1)](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/5caffce2-2dc0-4484-b271-01802762f45b)

---

## 기능 리스트
![Screenshot from 2024-03-23 13-21-43](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/118419026/688857a8-377a-4ab6-894c-53c0d00d7184)


## 시스템 구성도
![image](https://github.com/addinedu-ros-4th/deeplearning-repo-5/assets/162243554/7cf192ce-980b-4124-adb2-365c06622897)

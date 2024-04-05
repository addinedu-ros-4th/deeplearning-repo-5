import pandas as pd

daily_words = [
    "안녕하세요",
    "고마워요",
    "죄송합니다",
    "괜찮아요",
    "미안해요",
    "자요",
    "안녕히",
    "가세요",
    "부탁드려요",
    "음료수",
    "메뉴판",
    "앉을게요",
    "좋아해요",
    "좋아하지",
    "사랑해요",
    "전화할게요",
    "날씨",
    "춥네요",
    "기분이",
    "생각해요",
    "놀러",
    "점심",
    "먹고",
    "음식점",
    "일정이",
    "커피",
    "영화",
    "하루",
    "화이팅",
    "힘내세요",
    "잘했어요",
    "기다려주세요",
    "시간이",
    "얼마나",
    "화장실",
    "도와주세요",
    "음식점",
    "추천해",
    "주변에",
    "마트가",
    "얼마인가요",
    "카드로",
    "식사",
    "물건",
    "옷을",
    "어디가",
    "비가",
    "춥겠네요",
    "더운",
    "더워요",
    "비가",
    "맑은",
    "옷을",
    "얼굴이",
    "턱이",
    "얼마예요",
    "현금으로",
    "계산서",
    "문을",
    "내려주세요",
    "여기에서",
    "비상구가",
    "길을",
    "반대",
    "마음이",
    "두통이",
    "목이",
    "다리가",
    "배가",
    "나빠요",
    "약을",
    "병원에",
    "어디서",
    "약국이"
]
daily_words_df = pd.DataFrame({'word': daily_words, 'frequency': 0})
daily_words_df.to_csv('/home/hj/amr_ws/ML_DL/src/project/deeplearning-repo-5/src/yhj/total/autocorrect.csv', index=False)
print('Reset csv File')
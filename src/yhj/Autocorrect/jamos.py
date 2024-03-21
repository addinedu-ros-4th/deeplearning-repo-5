from hangul_utils import join_jamos


# 자음-초성/종성
cons = {'ㄱ':'ㄱ', 'ㄴ':'ㄴ', 'ㄷ':'ㄷ',  'ㄹ':'ㄹ', 'ㅁ':'ㅁ', 'ㅂ':'ㅂ',  'ㅅ':'ㅅ', 
           'ㅇ':'ㅇ', 'ㅈ':'ㅈ',  'ㅊ':'ㅊ', 'ㅋ':'ㅋ', 'ㅌ':'ㅌ', 'ㅍ':'ㅍ', 'ㅎ':'ㅎ'}
cons_in_double = {'ㄱ':'ㄲ', 'ㄴ':'ㄴ', 'ㄷ':'ㄸ', 'ㄹ':'ㄹ', 'ㅁ':'ㅁ',  'ㅂ':'ㅃ',  'ㅅ':'ㅆ',
           'ㅇ':'ㅇ', 'ㅈ':'ㅉ', 'ㅊ':'ㅊ', 'ㅋ':'ㅋ', 'ㅌ':'ㅌ', 'ㅍ':'ㅍ', 'ㅎ':'ㅎ'}

# 모음-중성
vowels = {'ㅏ':'ㅏ', 'ㅐ':'ㅐ', 'ㅑ':'ㅑ', 'ㅒ':'ㅒ', 'ㅓ':'ㅓ', 'ㅔ':'ㅔ', 'ㅕ':'ㅕ', 'ㅖ':'ㅖ', 'ㅗ':'ㅗ', 'ㅗㅏ':'ㅘ', 'ㅗㅐ':'ㅙ', 'ㅗㅣ':'ㅚ',
           'ㅛ':'ㅛ', 'ㅜ':'ㅜ', 'ㅜㅓ':'ㅝ', 'ㅜㅔ':'ㅞ', 'ㅜㅣ':'ㅟ', 'ㅠ':'ㅠ',  'ㅡ':'ㅡ', 'ㅡㅣ':'ㅢ', 'ㅣ':'ㅣ'}

# 자음-종성
cons_double = {'ㄱㅅ':'ㄳ', 'ㄴㅈ':'ㄵ', 'ㄴㅎ':'ㄶ', 'ㄹㄱ':'ㄺ', 'ㄹㅁ':'ㄻ', 'ㄹㅂ':'ㄼ', 'ㄹㅅ':'ㄽ', 'ㄹㅌ':'ㄾ', 'ㄹㅍ':'ㄿ', 'ㄹㅎ':'ㅀ', 'ㅂㅅ':'ㅄ'}


def gesture2text(text):
    result = ''   # 영 > 한 변환 결과
    
    # 1. 해당 글자가 자음인지 모음인지 확인
    vc = '' 
    for t in text:
        if t in cons :
            vc+='c'
        elif t in vowels:
            vc+='v'
        else:
            vc+='!'
	
    # cvv → fVV / cv → fv / cc → dd  => 초성, 종성 분리
    vc = vc.replace('cvv', 'fVV').replace('cv', 'fv').replace('cc', 'dd')
	
    
    # 2. 자음 / 모음 / 두글자 자음 에서 검색
    i = 0
    while i < len(text):
        v = vc[i]
        t = text[i]

        j = 1
        # 한글일 경우
        try:
            if v == 'f' or v == 'c':   # 초성(f) & 자음(c) = 자음
                result+=cons[t]

            elif v == 'V':   # 더블 모음
                result+=vowels[text[i:i+2]]
                j+=1

            elif v == 'v':   # 모음
                result+=vowels[t]

            elif v == 'd':   # 더블 자음
                result+=cons_double[text[i:i+2]]
                j+=1
            else:
                result+=t
                
        # 한글이 아닐 경우
        except:
            if v in cons:
                result+=cons[t]
            elif v in vowels:
                result+=vowels[t]
            else:
                result+=t
        
        i += j


    return join_jamos(result)       

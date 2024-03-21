import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLabel
from PyQt6 import uic
from hangul_utils import join_jamos
from jamos import gesture2text, cons, vowels, cons_double, double_cons
import pandas as pd
from jamo import h2j, j2hcj
from gtts import gTTS
from playsound import playsound
import speech_recognition as sr


# UI 파일에서 생성된 클래스를 가져옴
from_class = uic.loadUiType("DL.ui")[0]

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        
    def get_words_with_prefix(self, prefix):
        if not prefix:  # 만약 접두사가 공백이면 빈 리스트를 반환
            return []

        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        words = []
        self._collect_words(node, prefix, words)
        return words
    
    def _collect_words(self, node, prefix, words):
        if node.is_end_of_word:
            words.append(prefix)
        
        for char, child_node in node.children.items():
            self._collect_words(child_node, prefix + char, words)

class MyMainWindow(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # UI 초기화 메소드 호출
        self.autoword_1.setVisible(False)
        self.autoword_2.setVisible(False)
        self.autoword_3.setVisible(False)
        self.autoword_4.setVisible(False)
        self.autoword_5.setVisible(False)
        self.text = ""
        self.prefix = ""
        self.file_name = "text_to_speech.mp3"
        self.trie = Trie()
        self.cons = cons
        self.vowels = vowels
        self.cons_double = cons_double
        self.flag = 0
        self.mt = ""
        self.setWindowTitle("Autocorrect")

        self.input.textChanged.connect(self.on_text_changed)

        self.autoword_1.clicked.connect(self.changeText_1)
        self.autoword_2.clicked.connect(self.changeText_2)
        self.autoword_3.clicked.connect(self.changeText_3)
        self.autoword_4.clicked.connect(self.changeText_4)
        self.autoword_5.clicked.connect(self.changeText_5)
        self.btn_reset.clicked.connect(self.reset_line)


        self.btn_ja_1.clicked.connect(self.add_ja_1)
        self.btn_ja_2.clicked.connect(self.add_ja_2)
        self.btn_ja_3.clicked.connect(self.add_ja_3)
        self.btn_ja_4.clicked.connect(self.add_ja_4)
        self.btn_ja_5.clicked.connect(self.add_ja_5)
        self.btn_ja_6.clicked.connect(self.add_ja_6)
        self.btn_mo_1.clicked.connect(self.add_mo_1)
        self.btn_mo_2.clicked.connect(self.add_mo_2)
        self.btn_mo_3.clicked.connect(self.add_mo_3)
        self.btn_mo_4.clicked.connect(self.add_mo_4)
        self.btn_mo_5.clicked.connect(self.add_mo_5)
        self.btn_mo_6.clicked.connect(self.add_mo_6)

        self.btn_shift.clicked.connect(self.add_shift)
        self.btn_question.clicked.connect(self.add_question)
        self.btn_bspace.clicked.connect(self.bspace)
        self.btn_space.clicked.connect(self.space)
        
    def add_question(self):
        self.input.insert("?")

    def bspace(self):
        text = self.input.text()
        if text:
            self.input.setText(text[:-1])  # 문자열의 마지막 문자 제거

    def space(self):
        self.input.insert(" ")  # 공백 추가
        
    def add_shift(self):
        self.flag = 1
        
    def add_ja_1(self):
        if self.flag == 1:
            self.input.insert("ㄲ")
            self.flag = 0
        else:
            self.input.insert("ㄱ")

    def add_ja_2(self):
        self.flag = 0
        self.input.insert("ㄴ")

    def add_ja_3(self):
        if self.flag == 1:
            self.input.insert("ㄸ")
            self.flag = 0
        else:
            self.input.insert("ㄷ")
            
    def add_ja_4(self):
        self.flag = 0
        self.input.insert("ㄹ")
        
    def add_ja_5(self):
        self.flag = 0
        self.input.insert("ㅁ")

    def add_ja_6(self):
        if self.flag == 1:
            self.input.insert("ㅃ")
            self.flag = 0
        else:
            self.input.insert("ㅂ")

    def add_mo_1(self):
        self.flag = 0
        self.input.insert("ㅏ")

    def add_mo_2(self):
        self.flag = 0
        self.input.insert("ㅑ")

    def add_mo_3(self):
        self.flag = 0
        self.input.insert("ㅓ")

    def add_mo_4(self):
        self.flag = 0
        self.input.insert("ㅕ")

    def add_mo_5(self):
        self.flag = 0
        self.input.insert("ㅗ")

    def add_mo_6(self):
        self.flag = 0
        self.input.insert("ㅛ")
        
    def reset_line(self):
        self.input.clear()  # Line edit의 문자열을 삭제합니다.


    def speech_word(self, word_to_speech) :
        tts_ko = gTTS(text=word_to_speech, lang='ko')
        tts_ko.save(self.file_name)
        playsound(self.file_name)

    def add_word(self, input_word):
        if input_word.strip():  # 입력된 단어가 공백이 아닌지 확인
            word_df = pd.read_csv('autocorrect.csv')
            if input_word in word_df['word'].values:
                index = word_df.index[word_df['word'] == input_word].tolist()
                word_df['frequency'][index] += 1
                print("fre")
            else:
                word_df.loc[len(word_df)] = [input_word, 1]
                print("word")

            word_df.to_csv('autocorrect.csv', index=False)

    def changeText_1(self) :
        word = self.text.split()
        new_word = self.autoword_1.text()
        if word:
            word[-1] = new_word
            self.text = " ".join(word)
            self.text = self.text + " "
            self.input.setText(self.text)  
            self.add_word(new_word)
            
    def changeText_2(self) :
        word = self.text.split()
        new_word = self.autoword_2.text()
        if word:
            word[-1] = new_word
            self.text = " ".join(word)
            self.text = self.text + " "
            self.input.setText(self.text)
            self.add_word(new_word)  

    def changeText_3(self) :
        word = self.text.split()
        new_word = self.autoword_3.text()
        if word:
            word[-1] = new_word
            self.text = " ".join(word)
            self.text = self.text + " "
            self.input.setText(self.text)
            self.add_word(new_word)

    def changeText_4(self) :
        word = self.text.split()
        new_word = self.autoword_4.text()
        if word:
            word[-1] = new_word
            self.text = " ".join(word)
            self.text = self.text + " "
            self.input.setText(self.text)  
            self.add_word(new_word)

    def changeText_5(self) :
        word = self.text.split()
        new_word = self.autoword_5.text()
        if word:
            word[-1] = new_word
            self.text = " ".join(word)
            self.text = self.text + " "
            self.input.setText(self.text)  
            self.add_word(new_word)

    
            
    def on_text_changed(self):
        self.word_df=pd.read_csv('autocorrect.csv')
        self.words = self.word_df['word']
        self.text = self.input.text()
        self.text = j2hcj(h2j(self.text))
        if len(self.text) >= 2 and self.text[-2] in double_cons:  # 인덱스 접근 전에 길이 확인
            # 새로운 문자열을 생성하여 할당
            self.text = self.text[:-2] + double_cons[self.text[-2]] + self.text[-1] 

        self.text = gesture2text(self.text)

        for word in self.words:
            self.trie.insert(word)
        
        if self.text.strip():  # 입력이 공백이 아닌 경우에만 처리
            if self.text[-1] == " ":
                print("Space 입력이 감지되었습니다.")
                self.prefix = self.text.split(" ")[-2]
                print(self.prefix)
                self.speech_word(self.prefix)
                self.add_word(self.prefix)
            else:
                
                self.prefix = self.text.split(" ")[-1]
                #print(self.prefix)
                
                 
                self.input.setText(self.text)
                suggestions = self.trie.get_words_with_prefix(self.prefix)
                indices = [self.word_df.index[self.word_df['word'] == item].tolist() for item in suggestions]
                word_list_with_frequency = [(self.word_df.at[index[0], 'word'], self.word_df.at[index[0], 'frequency']) for index in indices]
                sorted_word_list = sorted(word_list_with_frequency, key=lambda x: x[1], reverse=True)
                suggestions = [word for word, _ in sorted_word_list]
                if suggestions:
                    if len(suggestions) > 5:
                        suggestions = suggestions[:5]
                    for i, suggestion in enumerate(suggestions, 1):
                        getattr(self, f'autoword_{i}').setText(suggestion)
                        getattr(self, f'autoword_{i}').setVisible(True)
                    for i in range(5-len(suggestions)):
                        getattr(self, f'autoword_{5-i}').setVisible(False)
                else : 
                    self.autoword_1.setVisible(False)
                    self.autoword_2.setVisible(False)
                    self.autoword_3.setVisible(False)
                    self.autoword_4.setVisible(False)
                    self.autoword_5.setVisible(False)


   

def main():
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

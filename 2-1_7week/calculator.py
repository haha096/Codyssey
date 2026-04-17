# pip install PyQt5
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


STYLE_OPERATOR = '''
    QPushButton {
        background-color: #ff9f0a;
        color: white;
        border-radius: 35px;
        border: none;
        font-size: 28px;
    }
    QPushButton:pressed {
        background-color: #ffcc7a;
    }
'''

STYLE_FUNCTION = '''
    QPushButton {
        background-color: #a5a5a5;
        color: black;
        border-radius: 35px;
        border: none;
        font-size: 20px;
    }
    QPushButton:pressed {
        background-color: #d4d4d4;
    }
'''

STYLE_NUMBER = '''
    QPushButton {
        background-color: #333333;
        color: white;
        border-radius: 35px;
        border: none;
        font-size: 24px;
    }
    QPushButton:pressed {
        background-color: #737373;
    }
'''

STYLE_ZERO = '''
    QPushButton {
        background-color: #333333;
        color: white;
        border-radius: 35px;
        border: none;
        font-size: 24px;
        text-align: left;
        padding-left: 28px;
    }
    QPushButton:pressed {
        background-color: #737373;
    }
'''


class Calculator(QWidget):
    """아이폰 스타일 계산기 UI 위젯."""

    # 객체가 생성될 때 한 번 자동으로 실행되는 초기화 메소드
    def __init__(self):
        super().__init__()
        self.display_text = '0'
        # 4칙 연산 상태 관리 변수 초기화
        self.first_number = 0.0      # 첫 번째 피연산자
        self.operator = None         # 현재 선택된 연산자
        self.waiting_second = False  # 두 번째 수 입력 대기 상태
        self._init_ui()

    def _init_ui(self):
        """UI 초기화: 디스플레이와 버튼 배치를 설정한다."""
        self.setWindowTitle('Calculator') # 창 제목
        self.setFixedSize(340, 580)       # 창 크기 고정
        self.setStyleSheet('background-color: #1c1c1e;') # 배경은 어두운 색으로

        main_layout = QVBoxLayout() # 세로 방향으로 쌓는 레이아웃
        main_layout.setSpacing(0)   # 위젯 사이 간격 0
        main_layout.setContentsMargins(12, 20, 12, 12) # 바깥 여백 (좌, 상, 우, 하)

        self.display = QLabel('0') # 숫자를 보여주는 텍스트 라벨
        self.display.setAlignment(Qt.AlignRight | Qt.AlignBottom) # 오른쪽 아래 정렬
        self.display.setFont(QFont('Arial', 64, QFont.Light))     # 폰트, 크기, 굵기
        self.display.setStyleSheet('color: white; padding-right: 8px;')
        self.display.setFixedHeight(160)    # 디스플레이 높이 고정
        main_layout.addWidget(self.display) # 레이아웃에 디스플레이 추가

        # ------------------ 버튼 UI ------------------
        grid = QGridLayout()
        grid.setSpacing(12)

        button_data = [
            ('AC',  0, 0, 1, STYLE_FUNCTION),
            ('+/-', 0, 1, 1, STYLE_FUNCTION),
            ('%',   0, 2, 1, STYLE_FUNCTION),
            ('÷',   0, 3, 1, STYLE_OPERATOR),
            ('7',   1, 0, 1, STYLE_NUMBER),
            ('8',   1, 1, 1, STYLE_NUMBER),
            ('9',   1, 2, 1, STYLE_NUMBER),
            ('×',   1, 3, 1, STYLE_OPERATOR),
            ('4',   2, 0, 1, STYLE_NUMBER),
            ('5',   2, 1, 1, STYLE_NUMBER),
            ('6',   2, 2, 1, STYLE_NUMBER),
            ('-',   2, 3, 1, STYLE_OPERATOR),
            ('1',   3, 0, 1, STYLE_NUMBER),
            ('2',   3, 1, 1, STYLE_NUMBER),
            ('3',   3, 2, 1, STYLE_NUMBER),
            ('+',   3, 3, 1, STYLE_OPERATOR),
            ('0',   4, 0, 2, STYLE_ZERO),
            ('.',   4, 2, 1, STYLE_NUMBER),
            ('=',   4, 3, 1, STYLE_OPERATOR),
        ]

        for label, row, col, colspan, style in button_data:
            btn = QPushButton(label)
            btn.setFixedHeight(70)
            btn.setStyleSheet(style)

            if colspan == 2:
                btn.setFixedWidth(152)
                grid.addWidget(btn, row, col, 1, colspan)
            else:
                grid.addWidget(btn, row, col)

            btn.clicked.connect(
                lambda checked, text=label: self._on_button_clicked(text)
            )

        main_layout.addLayout(grid)
        self.setLayout(main_layout)
        # ------------------ 버튼 UI ------------------

    def _on_button_clicked(self, text):
        """버튼 클릭 이벤트를 처리하고 디스플레이를 갱신한다."""
        # 누른 버튼을 text라는 변수에 저장
        if text == 'AC':
            # AC 클릭 시 연산 상태도 함께 초기화
            self.display_text = '0'
            self.first_number = 0.0
            self.operator = None
            self.waiting_second = False

        # 부호반전
        # text변수가 0이 아닐 때와 -일 때를 조건으로 삼아
        # 현재 수의 부호를 반전
        elif text == '+/-':
            if self.display_text != '0':
                if self.display_text.startswith('-'):
                    # '-' 제거
                    self.display_text = self.display_text[1:]
                else:
                    # '-' 추가
                    self.display_text = '-' + self.display_text

        # 퍼센트 변환
        # 50%로 누르면 0.5가 됨
        elif text == '%':
            # % 클릭 시 현재 숫자를 100으로 나눠 퍼센트 변환
            value = float(self.display_text) / 100
            self.display_text = self._format(value)

        # 연산자 - 첫번째 수 저장
        elif text in ('÷', '×', '-', '+'):
            # 연산자 클릭 시 첫 번째 수와 연산자를 저장하고 대기 상태로 전환
            self.first_number = float(self.display_text)
            self.operator = text
            self.waiting_second = True

        # 계산실행
        elif text == '=':
            # = 클릭 시 저장된 첫 번째 수, 연산자, 현재 수로 계산 실행
            if self.operator is not None: # 연산자가 있을 때만 계산
                second_number = float(self.display_text)
                result = self._calculate(self.first_number, self.operator, second_number)
                self.display_text = self._format(result)
                self.operator = None
                self.waiting_second = False

        elif text == '.':
            if self.waiting_second:
                self.display_text = '0.'
                self.waiting_second = False
            elif '.' not in self.display_text:
                self.display_text += '.'

        # 흐름을 전체적으로 보면
        # 3을 입력
        # first_number = 0.0 | operator = None | display_text = '3'

        # +를 입력
        # first_number = 3.0 | operator = '+' | display_text = '3'

        # 5를 입력
        # first_number = 3.0 | operator = None | display_text = '5'

        # =을 입력
        # first_number = 0.0 | operator = None | display_text = '8'


        else:
            # 연산자 입력 후 첫 숫자 클릭이면 디스플레이를 새 숫자로 교체
            if self.display_text == '0' or self.waiting_second:
                self.display_text = text
                self.waiting_second = False
            else:
                self.display_text += text

        self.display.setText(self.display_text)

    def _calculate(self, a, operator, b):
        """두 수와 연산자를 받아 4칙 연산 결과를 반환한다."""
        if operator == '+':
            return a + b
        elif operator == '-':
            return a - b
        elif operator == '×':
            return a * b
        elif operator == '÷':
            # 0으로 나누는 경우 예외 처리
            if b == 0:
                return 0.0
            return a / b
        return 0.0

    def _format(self, value):
        """숫자를 디스플레이용 문자열로 변환한다. 정수면 소수점을 제거한다."""
        if value == int(value):
            return str(int(value))
        return str(value)


if __name__ == '__main__':
    app = QApplication([])
    calc = Calculator()
    calc.show()
    app.exec_()
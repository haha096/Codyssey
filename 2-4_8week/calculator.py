"""
PyQt5를 활용한 iOS 스타일 계산기
PEP 8 스타일 가이드를 준수하여 작성
외부 라이브러리 없이 PyQt5만 사용 (sys 미사용)
"""

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QGridLayout, QVBoxLayout, QPushButton, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


# =============================================================================
# Calculator 클래스
# 계산기의 모든 비즈니스 로직을 담당한다.
# UI와 완전히 분리되어 순수 연산 로직만 포함한다.
# =============================================================================
class Calculator:
    """
    계산기 로직을 담당하는 클래스.

    구현 항목:
    - 수행과제 1, 2 : add(), subtract(), multiply(), divide() 사칙연산 메소드
    - 수행과제 3     : reset(), negative_positive(), percent() 메소드
    - 수행과제 4     : input_digit() - 숫자 키 누를 때마다 화면에 숫자 누적
    - 수행과제 5     : input_decimal() - 소수점 입력 (중복 방지)
    - 수행과제 6     : equal() - 결과 계산 및 반환
    제약사항         : 0 나누기, 숫자 범위 초과 예외 처리 포함
    """

    def __init__(self):
        self._current_input = '0'      # 현재 화면에 표시 중인 숫자 문자열
        self._previous_input = None    # 연산자 입력 전 저장된 숫자
        self._operator = None          # 현재 선택된 연산자 (+, -, ×, ÷)
        self._new_number = True        # True 이면 다음 숫자 입력 시 새 수 시작
        self._just_calculated = False  # equal() 직후 상태 추적

    # -------------------------------------------------------------------------
    # 사칙연산 메소드
    #
    # 설계: 각 메소드는 a, b 두 수를 받아 연산 결과를 반환한다.
    # 연산 후 _validate_result()로 수치 유효성(무한대·NaN)을 검사한다.
    # 이를 통해 제약사항인 '처리 가능한 숫자 범위 초과' 예외를 처리한다.
    # -------------------------------------------------------------------------

    def add(self, a, b):
        """덧셈 연산: a + b를 계산하고 검증 후 반환한다."""
        result = a + b
        self._validate_result(result)
        return result

    def subtract(self, a, b):
        """뺄셈 연산: a - b를 계산하고 검증 후 반환한다."""
        result = a - b
        self._validate_result(result)
        return result

    def multiply(self, a, b):
        """곱셈 연산: a × b를 계산하고 검증 후 반환한다."""
        result = a * b
        self._validate_result(result)
        return result

    def divide(self, a, b):
        """
        나눗셈 연산: a ÷ b를 계산하고 검증 후 반환한다.
        제약사항: b == 0 이면 ZeroDivisionError를 발생시킨다.
        """
        if b == 0:
            raise ZeroDivisionError('0으로 나눌 수 없습니다.')
        result = a / b
        self._validate_result(result)
        return result

    # -------------------------------------------------------------------------
    # 초기화·부호 전환·퍼센트 메소드
    #
    # 설계: 각 메소드는 _current_input 상태를 직접 변경한다.
    # - reset()           : 모든 내부 상태를 초기값으로 되돌린다.
    # - negative_positive(): 현재 숫자의 부호를 반전한다 (양수 ↔ 음수).
    # - percent()         : 현재 숫자를 100으로 나눠 퍼센트 값으로 변환한다.
    # -------------------------------------------------------------------------

    def reset(self):
        """AC(All Clear): 모든 연산 상태를 초기화한다."""
        self._current_input = '0'
        self._previous_input = None
        self._operator = None
        self._new_number = True
        self._just_calculated = False

    def negative_positive(self):
        """
        +/- 부호 전환 메소드.
        현재 입력값을 float으로 변환 후 부호를 반전하고
        _format_number()로 다시 문자열로 변환하여 저장한다.
        """
        value = float(self._current_input)
        toggled = -value
        self._current_input = self._format_number(toggled)

    def percent(self):
        """
        % 퍼센트 메소드.
        현재 입력값을 100으로 나누어 퍼센트 값으로 변환한다.
        예: 50 → 0.5
        """
        value = float(self._current_input)
        result = value / 100
        self._current_input = self._format_number(result)

    # -------------------------------------------------------------------------
    # 숫자 누적 입력
    #
    # 설계: _new_number 플래그로 '새 숫자 시작'과 '기존 숫자에 누적'을 구분한다.
    # - _new_number == True  : 새 숫자를 시작한다 (기존 값 덮어씀).
    # - _new_number == False : 기존 문자열 뒤에 숫자를 이어 붙인다.
    # 입력 자리 수는 최대 15자리로 제한한다.
    # -------------------------------------------------------------------------

    def input_digit(self, digit):
        """
        숫자 버튼 입력 처리.
        버튼을 누를 때마다 화면의 숫자가 누적된다.
        """
        digit = str(digit)
        if self._new_number:
            self._current_input = digit
            self._new_number = False
        else:
            # 부호(-)와 소수점(.)을 제외한 순수 숫자 자리 수 제한
            pure_digits = self._current_input.replace('-', '').replace('.', '')
            if len(pure_digits) < 15:
                self._current_input += digit
        self._just_calculated = False

    # -------------------------------------------------------------------------
    # 소수점 입력 (중복 방지)
    #
    # 설계: '.' 이 이미 _current_input 에 포함되어 있으면 추가하지 않는다.
    # _new_number 상태에서 소수점을 누르면 '0.' 으로 시작한다.
    # -------------------------------------------------------------------------

    def input_decimal(self):
        """
        소수점(.) 버튼 입력 처리.
        이미 소수점이 입력된 상태에서는 추가로 입력되지 않는다.
        """
        if self._new_number:
            self._current_input = '0.'
            self._new_number = False
            return
        if '.' not in self._current_input:
            self._current_input += '.'

    # -------------------------------------------------------------------------
    # 결과 출력 메소드
    #
    # 설계: _operator와 _previous_input을 이용해 계산을 수행한다.
    # - 연산자나 이전 입력이 없으면 현재 값을 그대로 반환한다.
    # - 예외(0 나누기, 범위 초과)는 내부에서 처리하고 오류 메시지를 반환한다.
    # 계산 완료 후 _new_number = True, _just_calculated = True 로 상태를 전환한다.
    # -------------------------------------------------------------------------

    # = 버튼 처리: 저장된 연산자와 피연산자로 결과를 계산하여 반환한다.
    # 수학적 예외(ZeroDivisionError, OverflowError)는 내부에서 처리한다.
    
    def equal(self):
        if self._operator is None or self._previous_input is None:
            return self._current_input

        a = float(self._previous_input)
        b = float(self._current_input)

        try:
            if self._operator == '+':
                result = self.add(a, b)
            elif self._operator == '-':
                result = self.subtract(a, b)
            elif self._operator == '×':
                result = self.multiply(a, b)
            elif self._operator == '÷':
                result = self.divide(a, b)
            else:
                return self._current_input

        except ZeroDivisionError:
            # 제약사항: 0 나누기 예외 처리
            self.reset()
            self._current_input = '오류: 0으로 나누기'
            return self._current_input

        except OverflowError:
            # 제약사항: 숫자 범위 초과 예외 처리
            self.reset()
            self._current_input = '범위 초과'
            return self._current_input

        except ValueError:
            self.reset()
            self._current_input = '오류'
            return self._current_input

        self._current_input = self._format_number(result)
        self._previous_input = None
        self._operator = None
        self._new_number = True
        self._just_calculated = True
        return self._current_input

    # -------------------------------------------------------------------------
    # 연산자 설정 (UI에서 호출)
    # -------------------------------------------------------------------------

    def set_operator(self, op):
        """
        연산자(+, -, ×, ÷) 설정.
        이미 이전 입력값이 있고 새 숫자가 아직 입력되지 않았으면
        먼저 equal()을 호출하여 연속 연산(ex: 3 + 5 × 2)을 처리한다.
        """
        if self._previous_input is not None and not self._new_number:
            self.equal()

        self._previous_input = self._current_input
        self._operator = op
        self._new_number = True

    # -------------------------------------------------------------------------
    # 상태 조회 메소드 (UI가 호출하는 인터페이스)
    # -------------------------------------------------------------------------

    def get_display(self):
        """현재 화면에 표시할 문자열을 반환한다."""
        return self._current_input

    def get_operator(self):
        """현재 선택된 연산자를 반환한다."""
        return self._operator

    # -------------------------------------------------------------------------
    # 내부 헬퍼 메소드
    # -------------------------------------------------------------------------

    def _validate_result(self, value):
        """
        제약사항: 수치 유효성 검사.
        - float('inf') / float('-inf') : OverflowError 발생
        - NaN (value != value 성질 이용): ValueError 발생
        math 라이브러리 없이 float의 특성만으로 검사한다.
        """
        if value == float('inf') or value == float('-inf'):
            raise OverflowError('처리할 수 있는 숫자의 범위를 초과했습니다.')
        if value != value:  # NaN은 자기 자신과 같지 않다는 IEEE 754 특성 활용
            raise ValueError('유효하지 않은 연산 결과입니다.')

    # [보너스 과제] 소수점 6자리 이하 반올림 처리
    def _format_number(self, value):
        """
        [보너스 과제] 숫자를 표시용 문자열로 변환한다.
        - 소수점 6자리 이하는 round()로 반올림하여 축약 표시
        - 정수로 표현 가능한 값은 소수점 없이 정수로 반환
        - f-string 포맷으로 끝의 불필요한 0을 제거
        """
        rounded = round(value, 6)

        # 정수로 표현 가능하면 소수점 없이 반환 (예: 3.0 → '3')
        if rounded == int(rounded):
            return str(int(rounded))

        # 소수점 6자리까지 표현 후 불필요한 후행 0 제거
        formatted = f'{rounded:.6f}'.rstrip('0')
        return formatted


# =============================================================================
# CalculatorWindow 클래스
# PyQt5로 UI를 구성하고 Calculator 클래스와 연결하여 완전한 동작을 구현한다.
# =============================================================================
class CalculatorWindow(QMainWindow):
    """
    계산기 UI 클래스.

    설계:
    - Calculator 인스턴스를 _calc 멤버로 보유한다.
    - 모든 버튼 클릭 이벤트는 _on_button_click()으로 통합 처리한다.
    - _on_button_click()은 버튼 텍스트에 따라 적절한 Calculator 메소드를 호출한다.
    - 보너스: 디스플레이 텍스트 길이에 따라 폰트 크기를 자동으로 조정한다.
    - 보너스: 현재 선택된 연산자 버튼을 반전 색상으로 강조 표시한다.
    """

    def __init__(self):
        super().__init__()
        self._calc = Calculator()      # Calculator 인스턴스 생성
        self._op_buttons = {}          # 연산자 버튼 참조 (강조 표시용)
        self._init_ui()

    def _init_ui(self):
        """UI 전체를 초기화한다."""
        self.setWindowTitle('Calculator')
        self.setFixedSize(380, 620)
        self.setStyleSheet('background-color: #1c1c1e;')

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 30, 12, 12)
        main_layout.setSpacing(0)

        # --- 디스플레이 레이블 ---
        self._display = QLabel('0')
        self._display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._display.setFixedHeight(160)
        self._display.setStyleSheet(
            'color: white;'
            'padding: 0px 16px;'
            'background-color: #1c1c1e;'
        )
        self._update_display_font()    # [보너스 과제] 초기 폰트 크기 설정
        main_layout.addWidget(self._display)

        # --- 버튼 그리드 ---
        grid = QGridLayout()
        grid.setSpacing(10)

        # 그리드 각 열이 동일한 비율로 늘어나도록 설정
        for col in range(4):
            grid.setColumnStretch(col, 1)
        for row in range(5):
            grid.setRowStretch(row, 1)

        # (표시 텍스트, 행, 열, 열 span, 버튼 유형)
        button_layout = [
            ('AC',  0, 0, 1, 'func'),
            ('+/-', 0, 1, 1, 'func'),
            ('%',   0, 2, 1, 'func'),
            ('÷',   0, 3, 1, 'op'),
            ('7',   1, 0, 1, 'num'),
            ('8',   1, 1, 1, 'num'),
            ('9',   1, 2, 1, 'num'),
            ('×',   1, 3, 1, 'op'),
            ('4',   2, 0, 1, 'num'),
            ('5',   2, 1, 1, 'num'),
            ('6',   2, 2, 1, 'num'),
            ('-',   2, 3, 1, 'op'),
            ('1',   3, 0, 1, 'num'),
            ('2',   3, 1, 1, 'num'),
            ('3',   3, 2, 1, 'num'),
            ('+',   3, 3, 1, 'op'),
            ('0',   4, 0, 2, 'zero'),   # 2칸 너비 (iOS 계산기 스타일)
            ('.',   4, 2, 1, 'num'),
            ('=',   4, 3, 1, 'eq'),
        ]

        for item in button_layout:
            text, row, col, span, btn_type = item
            btn = QPushButton(text)
            btn.setFixedHeight(72)

            # 유형별 색상 스타일 적용
            if btn_type == 'func':
                btn.setStyleSheet(self._make_btn_style('#a5a5a5', '#1c1c1e', '#d4d4d2'))
            elif btn_type == 'op':
                btn.setStyleSheet(self._make_btn_style('#ff9f0a', 'white', '#ffd780'))
                self._op_buttons[text] = btn         # 연산자 버튼 참조 저장
            elif btn_type == 'eq':
                btn.setStyleSheet(self._make_btn_style('#ff9f0a', 'white', '#ffd780'))
            elif btn_type == 'zero':
                # 0 버튼: 2칸 너비이므로 radius를 36px로 하면 pill(경기장) 모양
                btn.setStyleSheet(self._make_btn_style('#333333', 'white', '#636366', radius=36))
            else:  # 'num'
                btn.setStyleSheet(self._make_btn_style('#333333', 'white', '#636366'))

            grid.addWidget(btn, row, col, 1, span)

            # 버튼 클릭 시 _on_button_click() 연결
            # 람다의 기본 인자(t=text)로 클로저 캡처 문제를 방지한다.
            btn.clicked.connect(lambda checked, t=text: self._on_button_click(t))

        main_layout.addLayout(grid)

    def _make_btn_style(self, bg, fg, pressed_bg, radius=36):
        """
        QPushButton 스타일시트 문자열을 생성하여 반환한다.
        bg        : 기본 배경색
        fg        : 글자색
        pressed_bg: 눌렸을 때 배경색
        radius    : border-radius (0 버튼은 작은 값으로 pill 형태)
        """
        return (
            f'QPushButton {{'
            f'  background-color: {bg};'
            f'  color: {fg};'
            f'  border-radius: {radius}px;'
            f'  font-size: 26px;'
            f'  font-family: Arial;'
            f'}}'
            f'QPushButton:pressed {{'
            f'  background-color: {pressed_bg};'
            f'}}'
        )

    # -------------------------------------------------------------------------
    # UI 버튼 ↔ Calculator 클래스 연결
    #
    # 설계: 버튼 텍스트를 기준으로 분기하여 해당 Calculator 메소드를 호출한다.
    # 이로써 UI와 로직이 완전히 분리된 상태로 동작할 수 있다.
    # -------------------------------------------------------------------------

    def _on_button_click(self, text):
        """
        버튼 클릭 통합 핸들러.
        버튼 텍스트에 따라 Calculator의 메소드를 호출하고
        디스플레이와 연산자 버튼 강조를 갱신한다.
        """
        if text == 'AC':
            self._calc.reset()

        elif text == '+/-':
            self._calc.negative_positive()

        elif text == '%':
            self._calc.percent()

        elif text in ('+', '-', '×', '÷'):
            self._calc.set_operator(text)

        elif text == '=':
            self._calc.equal()

        elif text == '.':
            self._calc.input_decimal()

        else:
            # 숫자 버튼 (0~9)
            self._calc.input_digit(text)

        self._refresh_display()
        self._refresh_operator_highlight()

    def _refresh_display(self):
        """디스플레이 텍스트를 Calculator의 현재 값으로 갱신한다."""
        self._display.setText(self._calc.get_display())
        self._update_display_font()    # [보너스 과제] 텍스트 갱신마다 폰트 재조정

    # [보너스 과제] 출력값 길이에 따라 폰트 크기 자동 조정
    def _update_display_font(self):
        """
        [보너스 과제] 디스플레이 텍스트 길이에 따라 폰트 크기를 동적으로 조정한다.
        텍스트가 길수록 폰트 크기를 줄여 전체 내용이 한 줄에 표시되도록 한다.

        자리 수별 폰트 크기:
        ~6자리   → 72pt (기본)
        7~9자리  → 56pt
        10~12자리 → 44pt
        13~15자리 → 34pt
        16자리 이상 → 26pt (오류 메시지 등)
        """
        text = self._display.text() if self._display.text() else '0'
        length = len(text)

        if length <= 6:
            font_size = 64
        elif length <= 9:
            font_size = 52
        elif length <= 12:
            font_size = 40
        elif length <= 15:
            font_size = 32
        else:
            font_size = 24

        font = QFont('Arial', font_size, QFont.Light)
        self._display.setFont(font)

    def _refresh_operator_highlight(self):
        """
        현재 선택된 연산자 버튼을 반전 색상(흰 배경·주황 글자)으로 강조 표시한다.
        다른 연산자 버튼은 기본 스타일(주황 배경·흰 글자)로 복원한다.
        """
        current_op = self._calc.get_operator()
        for op_text, btn in self._op_buttons.items():
            if op_text == current_op:
                btn.setStyleSheet(self._make_btn_style('white', '#ff9f0a', '#e0e0e0'))
            else:
                btn.setStyleSheet(self._make_btn_style('#ff9f0a', 'white', '#ffd780'))


# =============================================================================
# 진입점 (sys 미사용: QApplication([]) 방식으로 실행)
# =============================================================================
if __name__ == '__main__':
    app = QApplication([])
    window = CalculatorWindow()
    window.show()
    app.exec_()
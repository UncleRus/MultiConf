.PHONY: clean all

include files.mk

############################################################
# Определение платформозависимых штук
############################################################

PYUIC = pyside-uic
PYRCC = pyside-rcc
RM = rm -f

############################################################
# Ниже этой строки не редактировать, если не понимаете,
# что делаете
############################################################

COMPILED_UI = $(UI_FILES:%.ui=%_ui.py)
COMPILED_RC = $(RC_FILES:%.qrc=%_rc.py)

all: res ui

res: $(COMPILED_RC)

ui: $(COMPILED_UI)

%_rc.py: %.qrc
	$(PYRCC) $< -o $@

%_ui.py: %.ui
	$(PYUIC) $< -o $@

clean:
	$(RM) $(COMPILED_UI) $(COMPILED_RC) $(COMPILED_UI:.py=.pyc) $(COMPILED_RC:.py=.pyc)

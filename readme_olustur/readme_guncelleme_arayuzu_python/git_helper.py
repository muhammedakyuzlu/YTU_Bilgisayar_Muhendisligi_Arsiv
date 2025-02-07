import subprocess
from degiskenler import SIL_BUTONU_STILI, EKLE_BUTONU_STILI
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QCheckBox,
    QMessageBox,
    QTextEdit,
    QLabel,
    QWidget,
    QSizePolicy,
    QHBoxLayout,
    QListWidgetItem,
    QSplitter,
)
from PyQt6.QtCore import Qt
import textwrap
from progress_dialog import CustomProgressDialogWithCancel
from threadler import CMDScriptRunnerThread


class GitHelper:
    @staticmethod
    def set_git_quotepath_off(repo_path):
        # Git yapılandırmasını değiştirmek için git config komutunu çağır
        subprocess.run(
            ["git", "-C", repo_path, "config", "core.quotepath", "off"], check=True
        )

    @staticmethod
    def git_status(repo_path):
        GitHelper.set_git_quotepath_off(repo_path)
        result = subprocess.run(
            ["git", "-C", repo_path, "status", "--porcelain"],
            capture_output=True,
            text=False,  # Bu satırı kaldırdık
        )
        # stdout'u 'utf-8' kullanarak decode ediyoruz
        decoded_output = result.stdout.decode("utf-8")
        return decoded_output.split("\n")

    @staticmethod
    def git_add(repo_path, file_path):
        if file_path[0] != '"':
            file_path = '"' + file_path + '"'
        subprocess.run(f"git -C {repo_path} add {file_path}", shell=True)

    @staticmethod
    def git_add_all(repo_path):
        subprocess.run(f"git -C {repo_path} add --all", shell=True)

    @staticmethod
    def git_reset_all(repo_path):
        subprocess.run(f"git -C {repo_path} reset HEAD", shell=True)

    @staticmethod
    def git_reset(repo_path, file_path):
        if file_path[0] != '"':
            file_path = '"' + file_path + '"'
        subprocess.run(f"git -C {repo_path} reset {file_path}", shell=True)

    @staticmethod
    def git_commit(repo_path, message):
        subprocess.run(["git", "-C", repo_path, "commit", "-m", message])

    @staticmethod
    def git_push(repo_path):
        subprocess.run(["git", "-C", repo_path, "push"])

    @staticmethod
    def git_restore(repo_path, file_path):
        subprocess.run(["git", "-C", repo_path, "restore", "file_path"])

    @staticmethod
    def git_diff(repo_path, file_name):
        # Git diff komutunu çalıştır
        result = subprocess.run(
            ["git", "-C", repo_path, "diff", file_name], capture_output=True, text=True
        )
        diff_output = result.stdout
        return diff_output


def getMaxSizeYatay():
    return QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)


def getMaxSizeDikey():
    return QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)


class GitDialog(QDialog):
    def __init__(self, repo_path, parent=None):
        super().__init__(parent=parent)
        self.setModal(True)
        self.repo_path = repo_path
        self.setMinimumSize(550, 650)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Git Değişiklikleri")
        self.setGeometry(100, 100, 600, 400)
        # Kaydedilmeyen ve Kaydedilen Değişiklikler için QSplitter oluştur
        changesSplitter = QSplitter(Qt.Orientation.Vertical)
        layout = QVBoxLayout()
        staged_layout = QHBoxLayout()
        unstaged_layout = QHBoxLayout()
        self.unstagedList = QListWidget()
        self.stagedList = QListWidget()
        self.commitMessage = QTextEdit()
        self.amendCheckBox = QCheckBox("Amend")
        self.amendCheckBox.setEnabled(False)
        pushButton = QPushButton("Değişiklikleri Pushla")
        add_all_btn = QPushButton("Tüm değişiklikleri ekle")
        add_all_btn.setStyleSheet(EKLE_BUTONU_STILI)
        unstaged_label = QLabel("Kaydedilmeyen Değişiklikler")
        unstaged_label.setSizePolicy(getMaxSizeYatay())
        unstaged_layout.addWidget(unstaged_label)
        unstaged_layout.addWidget(add_all_btn)
        unstaged_widget = QWidget()
        unstaged_widget.setLayout(unstaged_layout)
        changesSplitter.addWidget(unstaged_widget)
        changesSplitter.addWidget(self.unstagedList)
        staged_label = QLabel("Kaydedilen Değişiklikler")
        staged_label.setSizePolicy(getMaxSizeYatay())
        delete_all_btn = QPushButton("Tüm değişiklikleri sil")
        delete_all_btn.setStyleSheet(SIL_BUTONU_STILI)
        staged_layout.addWidget(staged_label)
        staged_layout.addWidget(delete_all_btn)
        staged_widget = QWidget()
        staged_widget.setLayout(staged_layout)
        changesSplitter.addWidget(staged_widget)
        changesSplitter.addWidget(self.stagedList)
        layout.addWidget(changesSplitter)
        layout.addWidget(QLabel("Commit Mesajı"))
        layout.addWidget(self.commitMessage)
        layout.addWidget(self.amendCheckBox)
        layout.addWidget(pushButton)
        self.setLayout(layout)
        self.stagedList.setSizePolicy(getMaxSizeDikey())
        self.unstagedList.setSizePolicy(getMaxSizeDikey())
        add_all_btn.clicked.connect(self.tumDegisiklikleriEkle)
        pushButton.clicked.connect(self.pushChanges)
        delete_all_btn.clicked.connect(self.tumDegisiklikleriSil)
        self.populateChanges()

    def tumDegisiklikleriEkle(self):
        if len(self.unstagedList) == 0:
            QMessageBox.warning(self, "Hata", "Eklenecek eleman bulunamadı")
            return

        reply = QMessageBox.question(
            self,
            "Emin Misiniz?",
            "Tüm değişiklikleri kaydetmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.No:
            QMessageBox.information(
                self, "İptal Edildi", "Tüm değişiklikleri kaydetme işlemi iptal edildi."
            )
            return

        for unstagedItem in self.getItemsFromListWidget(self.unstagedList):
            unstagedItem.onButtonClick()
        GitHelper.git_add_all(self.repo_path)

    def tumDegisiklikleriSil(self):
        if len(self.stagedList) == 0:
            QMessageBox.warning(self, "Hata", "Silinecek eleman bulunamadı")
            return
        reply = QMessageBox.question(
            self,
            "Emin Misiniz?",
            "Tüm değişiklikleri itap etmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.No:
            QMessageBox.information(
                self, "İptal Edildi", "Tüm değişiklikleri iptal işlemi iptal edildi."
            )
            return

        for unstagedItem in self.getItemsFromListWidget(self.stagedList):
            unstagedItem.onButtonClick()
        GitHelper.git_reset_all(self.repo_path)

    def populateChanges(self):
        status_lines = GitHelper.git_status(self.repo_path)
        for line in status_lines:
            if len(line) > 0:
                if line.startswith(" ") or line.startswith("??"):
                    self.addFileItem(self.unstagedList, line[3:], is_staged=False)
                else:
                    self.addFileItem(self.stagedList, line[3:], is_staged=True)

    def addFileItem(self, list_widget, file_name, is_staged):
        item = QListWidgetItem(list_widget)
        widget = FileItemWidget(file_name, is_staged, self)
        item.setSizeHint(widget.sizeHint())
        list_widget.addItem(item)
        list_widget.setItemWidget(item, widget)

    def getItemsFromListWidget(self, list_widget):
        items = []
        for index in range(list_widget.count()):
            item = list_widget.item(index)
            widget = list_widget.itemWidget(item)
            items.append(widget)
        return items

    def removeFileItem(self, list_widget, file_name):
        # Öğeler arasında döngü yap
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            widget = list_widget.itemWidget(item)
            # Dosya adını kontrol et
            if widget.file_name == file_name:
                # Öğeyi bulduğumuzda, onu ve widget'ını sil
                list_widget.takeItem(i)
                # Widget'ı bellekten tamamen kaldırmak için deleteLater kullanılır
                widget.deleteLater()
                break  # Eşleşme bulunduğunda döngüden çık

    def pushChanges(self):
        if self.stagedList.count() == 0:
            QMessageBox.warning(self, "Hata", "Kaydedilen dosya yok.")
            return

        commit_msg = self.commitMessage.toPlainText()
        if not commit_msg:
            QMessageBox.warning(self, "Hata", "Commit mesajı gir.")
            return
        reply = QMessageBox.question(
            self,
            "Emin Misiniz?",
            "Değişiklikleri pushlamak istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.No:
            QMessageBox.information(
                self, "İptal Edildi", "Pushlama işlemi iptal edildi."
            )
            return
        commit_msg = '"' + commit_msg + '"'
        self.commit_and_push(commit_msg=commit_msg)

    def commit_and_push(self, commit_msg):
        self.progress_dialog = CustomProgressDialogWithCancel(
            "Pushlanıyor", self, self.thread_durduruluyor
        )
        komut = f"git -C {self.repo_path} commit -m {commit_msg} && git -C {self.repo_path} push"
        # Thread'i başlat
        self.thread = CMDScriptRunnerThread(komut, "Git Push")
        self.thread.finished.connect(self.on_finished)
        self.thread.error.connect(self.on_error)
        self.thread.info.connect(self.info)
        self.thread.start()
        self.progress_dialog.show()

    def on_error(self, errors):
        self.progress_dialog.close()
        self.thread.quit()
        del self.thread
        del self.progress_dialog
        QMessageBox.critical(self, "Hata", errors)

    def info(self, message, maxlen=35):
        # Mesajı belirli bir uzunlukta parçalara ayır, kelimeleri tam böl
        wrapped_message = textwrap.fill(message, maxlen)

        # Güncellenmiş mesajı etiket metni olarak ayarla
        self.progress_dialog.setLabelText(wrapped_message)

    def on_finished(self, output):
        self.progress_dialog.close()
        self.thread.wait()
        del self.thread
        del self.progress_dialog
        self.close()
        QMessageBox.information(self, "Başarılı", output)

    def thread_durduruluyor(self):
        cevap = QMessageBox.question(
            self,
            "Onay",
            f"İşlemi durdurmak istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if cevap == QMessageBox.StandardButton.No:
            return
        self.progress_dialog.setLabelText("İşlem durduruluyor...")
        self.progress_dialog.setCancelButton(None)
        self.thread.durdur()


class FileItemWidget(QWidget):
    def __init__(self, file_name, is_staged, parent):
        super().__init__(parent)
        self.file_name = file_name
        self.is_staged = is_staged
        self.parent = parent
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        btn_layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setSizePolicy(getMaxSizeYatay())
        # burası güncellenecek restore buton eklenecek
        # burası güncellenecek restore buton eklenecek
        # burası güncellenecek restore buton eklenecek
        # burası güncellenecek restore buton eklenecek
        # burası güncellenecek restore buton eklenecek
        # burası güncellenecek restore buton eklenecek
        # burası güncellenecek restore buton eklenecek
        # burası güncellenecek restore buton eklenecek
        # burası güncellenecek restore buton eklenecek
        # burası güncellenecek restore buton eklenecek
        # burası güncellenecek restore buton eklenecek
        # burası güncellenecek restore buton eklenecek
        # burası güncellenecek restore buton eklenecek
        # burası güncellenecek restore buton eklenecek GitHelper.git_restore
        self.label.setText(self.elideText(self.file_name))
        self.label.setToolTip(self.file_name)  # Tam dosya adını tooltip olarak ekleme
        button = QPushButton("Kaydet" if not self.is_staged else "Sil")
        button.setStyleSheet(SIL_BUTONU_STILI if self.is_staged else EKLE_BUTONU_STILI)
        button.clicked.connect(self.onButtonClick)
        diff_btn = QPushButton("Farkı Gör")
        diff_btn.clicked.connect(self.showGitDiff)
        btn_layout.addWidget(button)
        btn_layout.addWidget(diff_btn)
        layout.addWidget(self.label)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def elideText(self, text, max_length=40):
        if len(text) <= max_length:
            return text
        else:
            keep_length = max_length - 3  # 3 karakter "..." için ayrıldı
            prefix_length = keep_length // 2
            suffix_length = keep_length - prefix_length
            return text[:prefix_length] + "..." + text[-suffix_length:]

    def onButtonClick(self):
        if self.is_staged:
            self.parent.removeFileItem(self.parent.stagedList, self.file_name)
            self.parent.addFileItem(
                self.parent.unstagedList, self.file_name, is_staged=not self.is_staged
            )
            GitHelper.git_reset(self.parent.repo_path, self.file_name)
        else:
            self.parent.removeFileItem(self.parent.unstagedList, self.file_name)
            self.parent.addFileItem(
                self.parent.stagedList, self.file_name, is_staged=not self.is_staged
            )
            GitHelper.git_add(self.parent.repo_path, self.file_name)

    def showGitDiff(self):
        diff_output = GitHelper.git_diff(self.parent.repo_path, self.file_name)
        diffWindow = DiffWindow(diff_output, diff_output, self)
        diffWindow.show()


class DiffWindow(QDialog):
    # DİFF GÖSTERİLMİYOR ŞU AN DÜZENLENECEK
    def __init__(self, old_text, new_text, parent=None):
        super().__init__(parent=parent)
        self.setModal(True)
        self.setMinimumSize(400, 400)
        self.old_text = old_text
        self.new_text = new_text
        self.initUI()

    def initUI(self):
        # Layoutları tanımla
        self.layout = QHBoxLayout()
        self.eski_layout = QVBoxLayout()
        self.yeni_layout = QVBoxLayout()

        self.eski_layout.addWidget(QLabel("Eskisi"))
        # Eski metni göster
        self.oldTextEdit = QTextEdit()
        self.oldTextEdit.setPlainText(self.old_text)
        self.oldTextEdit.setReadOnly(True)

        self.eski_layout.addWidget(self.oldTextEdit)
        self.yeni_layout.addWidget(QLabel("Yenisi"))
        # Yeni metni göster
        self.newTextEdit = QTextEdit()
        self.newTextEdit.setPlainText(self.new_text)
        self.newTextEdit.setReadOnly(True)
        self.yeni_layout.addWidget(self.newTextEdit)
        # Layoutlara widget'ları ekle
        self.layout.addLayout(self.eski_layout)
        self.layout.addLayout(self.yeni_layout)

        # Ana pencerenin layout'unu ayarla
        self.setLayout(self.layout)
        self.setWindowTitle("Fark Gösterici")

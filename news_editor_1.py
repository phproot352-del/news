# -*- coding: utf-8 -*-
"""Редактор новостей — Windows/Tkinter, база SQLite, импорт/экспорт JSON/CSV."""
import csv
import json
import os
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

APP_TITLE = "Редактор новостей"
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "news.db")

class NewsEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1200x760")
        self.minsize(980, 620)
        self.selected_id = None
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = sqlite3.Row
        self.init_db()
        self.configure_styles()
        self.build_menu()
        self.build_ui()
        self.load_categories()
        self.refresh_list()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def init_db(self):
        self.conn.execute("""CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Общее',
            author TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Черновик',
            published_at TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '',
            tags TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        self.conn.commit()

    def configure_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use('vista')
        except tk.TclError:
            pass
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'))
        style.configure('Sub.TLabel', foreground='#555555')
        style.configure('Treeview', rowheight=28, font=('Segoe UI', 10))
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))

    def build_menu(self):
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label='Новая новость', command=self.new_news, accelerator='Ctrl+N')
        file_menu.add_command(label='Сохранить', command=self.save_news, accelerator='Ctrl+S')
        file_menu.add_separator()
        file_menu.add_command(label='Экспорт JSON...', command=self.export_json)
        file_menu.add_command(label='Импорт JSON...', command=self.import_json)
        file_menu.add_command(label='Экспорт CSV...', command=self.export_csv)
        file_menu.add_separator()
        file_menu.add_command(label='Выход', command=self.on_close)
        menu.add_cascade(label='Файл', menu=file_menu)
        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label='О программе', command=lambda: messagebox.showinfo(APP_TITLE, 'Редактор новостей\nSQLite + Tkinter\nГотово для Windows'))
        menu.add_cascade(label='Справка', menu=help_menu)
        self.config(menu=menu)
        self.bind('<Control-n>', lambda e: self.new_news())
        self.bind('<Control-s>', lambda e: self.save_news())

    def build_ui(self):
        top = ttk.Frame(self, padding=(16, 12, 16, 8))
        top.pack(fill='x')
        ttk.Label(top, text=APP_TITLE, style='Title.TLabel').pack(side='left')
        ttk.Label(top, text='  Управление публикациями и черновиками', style='Sub.TLabel').pack(side='left', pady=(5, 0))
        ttk.Button(top, text='＋ Новая новость', style='Accent.TButton', command=self.new_news).pack(side='right')

        search = ttk.Frame(self, padding=(16, 0, 16, 10))
        search.pack(fill='x')
        ttk.Label(search, text='Поиск:').pack(side='left')
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search, textvariable=self.search_var, width=36)
        search_entry.pack(side='left', padx=(6, 12))
        search_entry.bind('<KeyRelease>', lambda e: self.refresh_list())
        ttk.Label(search, text='Статус:').pack(side='left')
        self.filter_status = ttk.Combobox(search, values=['Все', 'Черновик', 'На проверке', 'Опубликовано', 'Архив'], state='readonly', width=16)
        self.filter_status.set('Все')
        self.filter_status.pack(side='left', padx=6)
        self.filter_status.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())
        ttk.Button(search, text='Обновить', command=self.refresh_list).pack(side='left', padx=8)
        self.count_label = ttk.Label(search, text='')
        self.count_label.pack(side='right')

        main = ttk.PanedWindow(self, orient='horizontal')
        main.pack(fill='both', expand=True, padx=16, pady=(0, 16))
        left = ttk.Frame(main, padding=(0, 0, 10, 0))
        right = ttk.Frame(main, padding=(10, 0, 0, 0))
        main.add(left, weight=4)
        main.add(right, weight=6)

        cols = ('title', 'category', 'status', 'published_at')
        self.tree = ttk.Treeview(left, columns=cols, show='headings', selectmode='browse')
        headings = {'title':'Заголовок', 'category':'Рубрика', 'status':'Статус', 'published_at':'Дата'}
        widths = {'title':300, 'category':120, 'status':125, 'published_at':115}
        for col in cols:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor='w')
        scroll = ttk.Scrollbar(left, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        form = ttk.Frame(right)
        form.pack(fill='both', expand=True)
        form.columnconfigure(1, weight=1)
        form.rowconfigure(7, weight=1)
        ttk.Label(form, text='Карточка публикации', style='Title.TLabel').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 12))
        ttk.Label(form, text='Заголовок *').grid(row=1, column=0, sticky='w', pady=4)
        self.title_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.title_var).grid(row=1, column=1, sticky='ew', pady=4)
        ttk.Label(form, text='Рубрика').grid(row=2, column=0, sticky='w', pady=4)
        self.category_var = tk.StringVar(value='Общее')
        self.category_box = ttk.Combobox(form, textvariable=self.category_var, width=25)
        self.category_box.grid(row=2, column=1, sticky='w', pady=4)
        ttk.Label(form, text='Автор').grid(row=3, column=0, sticky='w', pady=4)
        self.author_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.author_var).grid(row=3, column=1, sticky='ew', pady=4)
        ttk.Label(form, text='Статус').grid(row=4, column=0, sticky='w', pady=4)
        self.status_var = tk.StringVar(value='Черновик')
        ttk.Combobox(form, textvariable=self.status_var, values=['Черновик', 'На проверке', 'Опубликовано', 'Архив'], state='readonly').grid(row=4, column=1, sticky='w', pady=4)
        ttk.Label(form, text='Дата публикации').grid(row=5, column=0, sticky='w', pady=4)
        self.date_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.date_var).grid(row=5, column=1, sticky='w', pady=4)
        ttk.Label(form, text='Теги').grid(row=6, column=0, sticky='w', pady=4)
        self.tags_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.tags_var).grid(row=6, column=1, sticky='ew', pady=4)
        ttk.Label(form, text='Краткое описание').grid(row=7, column=0, sticky='nw', pady=4)
        self.summary_text = ScrolledText(form, height=4, wrap='word', font=('Segoe UI', 10))
        self.summary_text.grid(row=7, column=1, sticky='nsew', pady=4)
        ttk.Label(form, text='Текст новости').grid(row=8, column=0, sticky='nw', pady=4)
        self.body_text = ScrolledText(form, height=14, wrap='word', font=('Segoe UI', 10))
        self.body_text.grid(row=8, column=1, sticky='nsew', pady=4)
        form.rowconfigure(8, weight=3)

        buttons = ttk.Frame(right)
        buttons.pack(fill='x', pady=(10, 0))
        ttk.Button(buttons, text='Сохранить', style='Accent.TButton', command=self.save_news).pack(side='left')
        ttk.Button(buttons, text='Предпросмотр', command=self.preview).pack(side='left', padx=8)
        ttk.Button(buttons, text='Удалить', command=self.delete_news).pack(side='right')

        self.new_news()

    def load_categories(self):
        rows = self.conn.execute("SELECT DISTINCT category FROM news WHERE category <> '' ORDER BY category").fetchall()
        cats = ['Общее', 'Политика редакции', 'Общество', 'Экономика', 'Технологии', 'Культура', 'Спорт']
        cats += [r['category'] for r in rows if r['category'] not in cats]
        self.category_box['values'] = cats

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        q = self.search_var.get().strip()
        status = self.filter_status.get()
        sql = "SELECT * FROM news WHERE 1=1"
        params = []
        if q:
            sql += " AND (title LIKE ? OR summary LIKE ? OR body LIKE ? OR tags LIKE ?)"
            params += [f'%{q}%'] * 4
        if status and status != 'Все':
            sql += " AND status=?"
            params.append(status)
        sql += " ORDER BY COALESCE(published_at, '') DESC, updated_at DESC, id DESC"
        rows = self.conn.execute(sql, params).fetchall()
        for row in rows:
            self.tree.insert('', 'end', iid=str(row['id']), values=(row['title'], row['category'], row['status'], row['published_at']))
        self.count_label.config(text=f'Записей: {len(rows)}')

    def clear_form(self):
        self.selected_id = None
        self.title_var.set('')
        self.category_var.set('Общее')
        self.author_var.set('')
        self.status_var.set('Черновик')
        self.date_var.set('')
        self.tags_var.set('')
        self.summary_text.delete('1.0', 'end')
        self.body_text.delete('1.0', 'end')
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def new_news(self):
        self.clear_form()
        self.title_var.set('Новая новость')
        self.author_var.set(os.environ.get('USERNAME', ''))
        self.date_var.set(datetime.now().strftime('%Y-%m-%d'))

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        row = self.conn.execute('SELECT * FROM news WHERE id=?', (int(selected[0]),)).fetchone()
        if row:
            self.selected_id = row['id']
            self.title_var.set(row['title'])
            self.category_var.set(row['category'])
            self.author_var.set(row['author'])
            self.status_var.set(row['status'])
            self.date_var.set(row['published_at'])
            self.tags_var.set(row['tags'])
            self.summary_text.delete('1.0', 'end'); self.summary_text.insert('1.0', row['summary'])
            self.body_text.delete('1.0', 'end'); self.body_text.insert('1.0', row['body'])

    def form_data(self):
        return {
            'title': self.title_var.get().strip(), 'category': self.category_var.get().strip() or 'Общее',
            'author': self.author_var.get().strip(), 'status': self.status_var.get(),
            'published_at': self.date_var.get().strip(), 'tags': self.tags_var.get().strip(),
            'summary': self.summary_text.get('1.0', 'end-1c').strip(),
            'body': self.body_text.get('1.0', 'end-1c').strip()
        }

    def save_news(self):
        data = self.form_data()
        if not data['title']:
            messagebox.showwarning('Проверка', 'Введите заголовок новости.')
            return
        now = datetime.now().isoformat(timespec='seconds')
        if self.selected_id:
            self.conn.execute("""UPDATE news SET title=?, category=?, author=?, status=?, published_at=?, summary=?, body=?, tags=?, updated_at=? WHERE id=?""",
                (data['title'], data['category'], data['author'], data['status'], data['published_at'], data['summary'], data['body'], data['tags'], now, self.selected_id))
        else:
            cur = self.conn.execute("""INSERT INTO news(title, category, author, status, published_at, summary, body, tags, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (data['title'], data['category'], data['author'], data['status'], data['published_at'], data['summary'], data['body'], data['tags'], now, now))
            self.selected_id = cur.lastrowid
        self.conn.commit(); self.load_categories(); self.refresh_list()
        self.tree.selection_set(str(self.selected_id)); self.tree.focus(str(self.selected_id))
        messagebox.showinfo('Готово', 'Новость сохранена.')

    def delete_news(self):
        if not self.selected_id:
            messagebox.showinfo('Удаление', 'Сначала выберите новость.')
            return
        if messagebox.askyesno('Удаление', 'Удалить выбранную новость?'):
            self.conn.execute('DELETE FROM news WHERE id=?', (self.selected_id,)); self.conn.commit()
            self.new_news(); self.refresh_list()

    def preview(self):
        data = self.form_data()
        win = tk.Toplevel(self); win.title('Предпросмотр — ' + (data['title'] or 'Без заголовка')); win.geometry('760x650')
        text = ScrolledText(win, wrap='word', font=('Segoe UI', 11), padx=24, pady=20)
        text.pack(fill='both', expand=True)
        text.insert('end', data['title'] + '\n', 'title')
        text.insert('end', f"{data['category']}  •  {data['published_at']}  •  {data['author']}\n\n", 'meta')
        if data['summary']: text.insert('end', data['summary'] + '\n\n', 'summary')
        text.insert('end', data['body'])
        text.config(state='disabled'); text.tag_config('title', font=('Segoe UI', 20, 'bold')); text.tag_config('meta', foreground='#666'); text.tag_config('summary', font=('Segoe UI', 12, 'italic'))

    def all_rows(self):
        return [dict(row) for row in self.conn.execute('SELECT * FROM news ORDER BY id').fetchall()]

    def export_json(self):
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON', '*.json')], initialfile='news_export.json')
        if path:
            with open(path, 'w', encoding='utf-8') as f: json.dump(self.all_rows(), f, ensure_ascii=False, indent=2)
            messagebox.showinfo('Экспорт', 'Данные экспортированы в JSON.')

    def import_json(self):
        path = filedialog.askopenfilename(filetypes=[('JSON', '*.json')])
        if not path: return
        try:
            with open(path, encoding='utf-8') as f: data = json.load(f)
            if not isinstance(data, list): raise ValueError('Ожидается массив новостей')
            now = datetime.now().isoformat(timespec='seconds')
            for item in data:
                title = str(item.get('title', '')).strip()
                if not title: continue
                self.conn.execute("INSERT INTO news(title, category, author, status, published_at, summary, body, tags, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (title, item.get('category','Общее'), item.get('author',''), item.get('status','Черновик'), item.get('published_at',''), item.get('summary',''), item.get('body',''), item.get('tags',''), now, now))
            self.conn.commit(); self.load_categories(); self.refresh_list(); messagebox.showinfo('Импорт', 'Импорт завершён.')
        except Exception as exc:
            messagebox.showerror('Ошибка импорта', str(exc))

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')], initialfile='news_export.csv')
        if path:
            rows = self.all_rows()
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id','title','category','author','status','published_at','summary','body','tags','created_at','updated_at'])
                writer.writeheader(); writer.writerows(rows)
            messagebox.showinfo('Экспорт', 'Данные экспортированы в CSV.')

    def on_close(self):
        self.conn.close(); self.destroy()

if __name__ == '__main__':
    NewsEditor().mainloop()

# log_analyzer.py readme

Скрипт предназначен для анализа логов ngnix и генерации отчета по времени выполнения запроса.
Разработан в рамках выполнения домашнего задания №1 по курсу Разработчик Python компании Отус.
Задание в файле homework.pdf

# Требования
- Python версии не ниже 3.2
- Шаблон отчета 'report.html', расположенный в каталоге скрипта
- Файл jquery.tablesorter.min.js, расположенный в каталоге REPORT_DIR

# Запуск и результат
Установка:

```console
$ git clone https://github.com/evgenykol/otus_py_01.git
```

Запуск:

```console
$ python3 log_analyzer.py
```

Скрипт ищет в каталоге LOG_DIR последний по дате в имени файла лог, обрабатывает его и пишет отчет в REPORT_DIR

При наличии конфиг-файла, запуск соответственно:

```console
$ python3 log_analyzer.py --config log_analyzer.cfg
```

# Запуск тестов

```console
$ python3 test_log_analyzer.py
```
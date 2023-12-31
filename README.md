# lapkino-stocks
### Python проект для обновления остатков интернет-магазина Lapkino на основе просмотра входящей почты с mail.ru через IMAP и гугл таблицы через Google API.
Протокол IMAP поддерживает критерий поиска до определенной даты "SENTSINCE", а так же многие другие критерии, но сервер mail.ru, из испробованных мною, отреагировал только на этот. На все другие, допустим столь важный FROM (отправитель), он отреагировал ошибкой (не поддерживается), так что приходится скачивать письма по одному и смотреть: можно ли его использовать (от нужного поставщика) и нужно ли остановиться (дальнейший поиск не имеет смысла).

### Алгоритм работы:

1) На основе данных гугл таблицы создается словарь где ключ - список почт поставщика, значение - параметры, по которым определяется как брать данные из excel файлов, а также останавливать ли по данному поставщику поиск. Если присутствует валидация артикулов (они они хоть немного совпадают с предыдущими - почти 100% это адекватные артикулы), то также скачиваются предыдущие артикулы либо целиком, либо часть. Если "Исключить" - TRUE, то поставщик игнорируется. Если что-то не так с данными из конфига - поставщик игнорируется, а строка с ним перекрашивается в красный.
2) Начинается последовательное скачивание писем. Для каждого из них совершается следующие действия:
 - Если это первое письмо - в какую нибудь переменную вставляется его дата. Она позже поставиться ненайденным поставщикам в "Поиск игнорируется до"
 - Все поставщики из словаря сверяются с датой письма. Если дата письма позже даты "Поиск игнорируется до" поставщика - поставщик удаляется из словаря. 
 - IF (отправитель письма входит в один из ключей словаря AND письмо имеет вложение AND вложение письма в формате .xls или .xlsx):
 - - Файл записывается из письма
 - - IF (в нужных столбцах есть значения AND (NOT валидация OR значения проходят валидации (артикулы - небольшая сверка с предыдущими, остатки - являются числами)):
 - - - Дата письма добавляется в словарь в какую нибудь переменную, она позже пойдет в "Дата последнего обновления", а данные остатков, после действий из ячеек "Действия с остатками" и "Действия с артикулами" вставляются в другой словарь, где ключ - лист поставщика, значение - данные. Поставщик удаляется из изначального словаря.

3) Таким образом, скачивание идет либо пока не закончатся поставщики из словаря (все поставщики найдены), либо пока не закончатся uid (писем больше нет. это значит что либо какие-то поставщики не найдены, либо последним письмом был последний поставщик). Все что осталось в первом списке - ненайденные поставщики, все что во втором - найденные.
4) Формируются данные для отправки в гугл таблицу:
 - Если есть листы в гугл таблице, которых нет в списке поставщиков - они удаляются.
 - Из первого словаря в конфиг у найденных поставщиков вставляется: "Найден" (FALSE), "Поиск игнорируется до" (дата последнего присланного письма ВООБЩЕ, то есть не только этого поставщика). 
 - Из второго словаря в конфиг идут: "Найден" (TRUE), "Дата последних остатков" (дата найденного письма) и "Дата последнего обновления" (понятно), а данные собственно остатков вставляются в лист поставщика, если его нет - создается новый.
#### Комментарии

- xlrd версии выше 1.2 не поддерживает открытие файлов .xlsx

- Для скачивания писем делаются следующие действия: 
1) Ограничивается диапазон: допустим, только определенная папка
2) Скачивается список uid (уникальный ключ письма) из диапазона с критерием SENTSINCE (до определенной даты, смотрите ниже). *Можно брать id, а не uid, но они меняются если в это время придет новое письмо. Из-за этого можно скачать ошибочное по устаревшему id.
3) Начинается поочередное скачивание писем по uid. Почему то mail.ru присылает uid в правильном порядке дат, но в неправильном порядке времени в пределе даты.

- Google API ограничивает количество запросов, так что лучше отправлять действия в таблице большими кусками.

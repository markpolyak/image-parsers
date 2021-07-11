## Парсинг изображений с shutterstock

[Ссылка на сайт](https://www.shutterstock.com/search?image_type=photo)

Для парсинга сайта необходимо создать объект класса ShutterstockParser и в качестве параметра передать путь к директории, в которую необходимо скачать изображения

```
shutterstockParser = ShutterstockParser(imageFolderPath="/Users/kirill/Desktop/image/")
```

Доступно 2 метода `parseAllPages` и `parsePage`, который в качестве параметра получает номер страницы (по умолчания номер странице равен 1)

```
shutterstockParser.parseAllPages()

shutterstockParser.parsePage()
```


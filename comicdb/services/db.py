from sqlalchemy import Column, String, Integer, Float, ForeignKey, Table, Integer, DateTime, create_engine, and_, or_
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from services.logger import create_logger
from services import constant
from dateutil.parser import parse
import datetime
from typing import (TYPE_CHECKING, Any, Dict, List, Type, Union, Optional,
                    ForwardRef)
import uuid

log = create_logger('database')

Base = declarative_base()

book_publisher = Table(
    "book_publisher",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("book.book_id")),
    Column("publisher_id", Integer, ForeignKey("publisher.publisher_id"))
)

book_author = Table(
    "book_author",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("book.book_id")),
    Column("author_id", Integer, ForeignKey("author.author_id"))
)

book_comment = Table(
    "book_comment",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("book.book_id")),
    Column("author_id", Integer, ForeignKey("comment.comment_id"))
)

book_series = Table(
    "book_series",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("book.book_id")),
    Column("series_id", Integer, ForeignKey("series.series_id"))
)

book_tag = Table(
    "book_tag",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("book.book_id")),
    Column("tag_id", Integer, ForeignKey("tag.tag_id"))
)


class Book(Base):
    __tablename__ = "book"
    book_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    authors = relationship(
        "Author", secondary=book_author, back_populates="books"
    )
    publisher = relationship(
        "Publisher", secondary=book_publisher, back_populates="books"
    )
    published = Column(DateTime)
    identifiers = Column(String)
    comments = relationship(
        "Comment", secondary=book_comment
    )
    languages = Column(String)
    series = relationship(
        "Series", secondary=book_series, back_populates="books"
    )
    series_id = Column(Integer)
    description = Column(String)
    tags = relationship(
        "Tag", secondary=book_tag, back_populates="books"
    )
    publishers = relationship(
        "Publisher", secondary=book_publisher, back_populates="books", overlaps="publisher"
    )
    rating = Column(Float)
    cover = Column(String)
    last_modified = Column(DateTime)
    is_read = Column(Integer)
    is_stared = Column(Integer)
    source = Column(String)
    uuid = Column(String)
    args = Column(String)
    url = Column(String)
    content_info = Column(String)
    file_type = Column(String)


class Author(Base):
    __tablename__ = "author"
    author_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    picture = Column(String)
    description = Column(String)
    books = relationship(
        "Book", secondary=book_author, back_populates="authors"
    )
    is_stared = Column(Integer)


class Publisher(Base):
    __tablename__ = "publisher"
    publisher_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    books = relationship(
        "Book", secondary=book_publisher, back_populates="publishers"
    )
    description = Column(String)
    is_stared = Column(Integer)


class Comment(Base):
    __tablename__ = "comment"
    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    content = Column(String)
    user_id = Column(Integer)


class Series(Base):
    __tablename__ = "series"
    series_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    books = relationship(
        "Book", secondary=book_series, back_populates="series"
    )


class Tag(Base):
    __tablename__ = "tag"
    tag_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    books = relationship(
        "Book", secondary=book_tag, back_populates="tags"
    )


engine = create_engine(constant.SQLITE_DB)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()


def create_all_db():
    Base.metadata.create_all(engine)
    log.info('Created all book info database')


def add_new_book(title: str,
                 published: datetime = datetime.datetime.now(),
                 identifiers: str = '',
                 languages: str = '',
                 publisher_name: str = '',
                 description: str = '',
                 rating: float = 0,
                 cover: str = 'data/covers/default.png',
                 last_modified: datetime = datetime.datetime.now(),
                 is_read: int = 0,
                 is_stared: int = 0,
                 source: str = '',
                 url: str = '',
                 file_type: str = '',
                 author_name: Union[str] = [],
                 tags: Union[str] = [],
                 content_info: str = '',
                 series_name: str = '',
                 *args, **kwargs) -> Book:
    book = (
        session.query(Book)
            .filter(Book.title == title)
            .filter(or_(Book.publishers == None, Book.publishers.any(Publisher.name == publisher_name)))
            .one_or_none()
    )
    if book is not None:
        log.debug(f"Book: {title} exists, skipped")
        return book
    else:
        book = Book(title=title,
                    published=published,
                    identifiers=identifiers,
                    languages=languages,
                    description=description,
                    rating=rating,
                    cover=cover,
                    last_modified=last_modified,
                    is_read=is_read,
                    is_stared=is_stared,
                    source=source,
                    url=url,
                    file_type=file_type,
                    content_info=content_info,
                    uuid=str(uuid.uuid1())
                    )
        session.add(book)
    publisher = (
        session.query(Publisher)
            .filter(Publisher.name == publisher_name)
            .one_or_none()
    )
    if publisher_name:
        if publisher is not None:
            log.debug(f"Publisher: {publisher_name} exists, skipped")
        else:
            publisher = Publisher(name=publisher_name, description='', is_stared=0)
            session.add(publisher)
        book.publishers.append(publisher)
        log.debug(f"Add publisher: {publisher_name}")
    if author_name:
        for single_author_name in author_name:
            author = (
                session.query(Author)
                    .filter(Author.name == single_author_name)
                    .one_or_none()
            )

            if author is not None:
                log.debug(f"Author: {single_author_name} exists, skipped")
                book.authors.append(author)
            else:
                author = Author(name=single_author_name, picture='data/author/default.png', description='', is_stared=0)
                session.add(author)
                book.authors.append(author)
                log.debug(f"Add author: {single_author_name}")

    for tag_name in tags:
        tag = (
            session.query(Tag)
                .filter(Tag.name == tag_name)
                .one_or_none()
        )
        if tag is not None:
            log.debug(f"Tag: {tag_name} exists, skipped")
        else:
            tag = Tag(name=tag_name)
            session.add(tag)
        book.tags.append(tag)
        log.debug(f"Add tag: {tag_name}")
    if series_name:
        series = (
            session.query(Series)
                .filter(Series.name == series_name)
                .one_or_none()
        )
        if series is not None:
            log.debug(f"Series: {series_name} exists, skipped")
        else:
            series = Series(name=series_name, description='')
        book.series.append(series)
    session.commit()
    return book


def get_book_by_id(book_id: int) -> Book:
    book = session.query(Book).filter(Book.book_id == book_id).one_or_none()
    return book


def get_series_by_id(series_id: int) -> Series:
    series = session.query(Series).filter(Series.series_id == series_id).one_or_none()
    return series


def get_comment_by_id(comment_id: int) -> Comment:
    comment = session.query(Comment).filter(Comment.content_id == comment_id).one_or_none()
    return comment


def get_publisher_by_id(publisher_id: int) -> Publisher:
    publisher = session.query(Publisher).filter(Publisher.publisher_id == publisher_id).one_or_none()
    return publisher


def get_author_by_id(author_id: int) -> Author:
    author = session.query(Author).filter(Author.author_id == author_id).one_or_none()
    return author


def update_book_info(book_id, **kwargs) -> [Book, None]:
    book = session.query(Book).filter(Book.book_id == book_id).one_or_none()
    if book is None:
        return book
    for key in kwargs:
        if key == 'author_name':
            book.authors = []
            for author_name in kwargs[key]:
                author = (
                    session.query(Author)
                        .filter(Author.name == author_name)
                        .one_or_none()
                )

                if author is not None:
                    log.debug(f"Author: {kwargs[key]} exists, skipped")
                else:
                    author = Author(name=kwargs[key], picture='data/author/default.png', description='', is_stared=0)
                    session.add(author)
                book.authors.append(author)
        elif key == 'publisher_name':
            publisher = (
                session.query(Publisher)
                    .filter(Publisher.name == kwargs[key])
                    .one_or_none()
            )

            if publisher is not None:
                log.debug(f"Publisher: {kwargs[key]} exists, skipped")
            else:
                publisher = Publisher(name=kwargs[key], description='', is_stared=0)
                session.add(publisher)
            book.publishers.append(publisher)
            log.debug(f"Add publisher: {kwargs[key]}")
        elif key == 'series_name':
            book.series = []
            series = (
                session.query(Series)
                    .filter(Series.name == kwargs[key])
                    .one_or_none()
            )
            if series is not None:
                log.debug(f"Series: {kwargs[key]} exists, skipped")
            else:
                series = Series(name=kwargs[key], description='')
            book.series.append(series)
        else:
            setattr(book, key, kwargs[key])
    session.add(book)
    session.commit()
    return book


class BookListQuery:
    @classmethod
    def get_books_by_time(cls, page: int = 0, page_size: int = 30) -> List[Book]:
        q = session.query(Book).offset(page * page_size).limit(page_size)
        return q

    @classmethod
    def get_books_by_author(cls, page: int = 0, page_size: int = 30, auther_name: str = '') -> List[Book]:
        q = (session.query(Book)
             .filter(Book.authors.any(Author.name == auther_name))
             .offset(page * page_size)
             .limit(page_size))
        return q

    @classmethod
    def get_books_by_name(cls, page: int = 0, page_size: int = 30, book_name: str = '') -> List[Book]:
        q = (session.query(Book)
             .filter(Book.title == book_name)
             .offset(page * page_size)
             .limit(page_size))
        return q

    @classmethod
    def get_books_by_series(cls, page: int = 0, page_size: int = 30, series_name: str = '') -> List[Book]:
        q = (session.query(Book)
             .filter(Book.series.any(Series.name == series_name))
             .offset(page * page_size)
             .limit(page_size))
        return q

    @classmethod
    def get_books_by_tag(cls, page: int = 0, page_size: int = 30, tag_name: str = '') -> List[Book]:
        q = (session.query(Book)
             .filter(Book.tags.any(Tag.name == tag_name))
             .offset(page * page_size)
             .limit(page_size))
        return q

    @classmethod
    def get_books_by_like_name(cls, page: int = 0, page_size: int = 30, book_name: str = '') -> List[Book]:
        q = (session.query(Book)
             .filter(Book.title.contains(book_name))
             .offset(page * page_size)
             .limit(page_size))
        return q

    @classmethod
    def get_books_by_like_author(cls, page: int = 0, page_size: int = 30, auther_name: str = '') -> List[Book]:
        q = (session.query(Book)
             .filter(Book.authors.any(Author.name.contains(auther_name)))
             .offset(page * page_size)
             .limit(page_size))
        return q

    @classmethod
    def get_books_by_like_series(cls, page: int = 0, page_size: int = 30, series_name: str = '') -> List[Book]:
        q = (session.query(Book)
             .filter(Book.series.any(Series.name.contains(series_name)))
             .offset(page * page_size)
             .limit(page_size))
        return q

    @classmethod
    def get_books_by_like_tag(cls, page: int = 0, page_size: int = 30, tag_name: str = '') -> List[Book]:
        q = (session.query(Book)
             .filter(Book.tags.any(Tag.name.contains(tag_name)))
             .offset(page * page_size)
             .limit(page_size))
        return q


class UpdateBookInfoQuery:
    @classmethod
    def update_cover(cls, file_path: str, book_id: int) -> bool:
        book = (session.query(Book)
                .filter(Book.book_id == book_id)
                .one_or_none())
        if not book:
            return False
        book.cover = file_path
        session.add(book)
        session.commit()
        return True

    @classmethod
    def update_info(cls, book_id: int,
                    title: str = '',
                    published: str = '',
                    identifiers: str = '',
                    languages: str = '',
                    publisher_name: List = [],
                    description: str = '',
                    rating: str = 0,
                    last_modified: str = '',
                    is_read: int = 0,
                    is_stared: int = 0,
                    source: str = '',
                    url: str = '',
                    series_id: str = '',
                    file_type: str = '',
                    author_name: List = [],
                    tags: Union[str] = [],
                    content_info: str = '',
                    series_name: List = [],
                    *args, **kwargs) -> bool:
        book = (session.query(Book)
                .filter(Book.book_id == book_id)
                .one_or_none())
        if not book:
            return False
        if title:
            book.title = title
        if published:
            book.published = parse(published)
        if identifiers:
            book.identifiers = identifiers
        if languages:
            book.languages = languages
        if publisher_name and publisher_name != ['']:
            book.publishers = []
            for single_publisher_name in publisher_name:
                publisher = (
                    session.query(Publisher)
                        .filter(Publisher.name == single_publisher_name)
                        .one_or_none()
                )
                if publisher is not None:
                    log.debug(f"Publisher: {single_publisher_name} exists, skipped")
                    book.publishers.append(publisher)
                else:
                    publisher = Publisher(name=single_publisher_name, description='', is_stared=0)
                    session.add(publisher)
                    book.publishers.append(publisher)
                    log.debug(f"Add Publisher: {single_publisher_name}")
        if description:
            book.description = description
        if rating:
            book.rating = float(rating)
        if source:
            book.source = source
        if file_type:
            book.file_type = file_type
        if author_name and author_name != ['']:
            book.authors = []
            for single_author_name in author_name:
                author = (
                    session.query(Author)
                        .filter(Author.name == single_author_name)
                        .one_or_none()
                )

                if author is not None:
                    log.debug(f"Author: {single_author_name} exists, skipped")
                    book.authors.append(author)
                else:
                    author = Author(name=single_author_name, picture='data/author/default.png', description='',
                                    is_stared=0)
                    session.add(author)
                    book.authors.append(author)
                    log.debug(f"Add author: {single_author_name}")
        if tags and tags != ['']:
            book.tags = []
            for tag_name in tags:
                tag = (
                    session.query(Tag)
                        .filter(Tag.name == tag_name)
                        .one_or_none()
                )
                if tag is not None:
                    log.debug(f"Tag: {tag_name} exists, skipped")
                else:
                    tag = Tag(name=tag_name)
                    session.add(tag)
                book.tags.append(tag)
                log.debug(f"Add tag: {tag_name}")
        if series_name and series_name != ['']:
            book.series = []
            for my_series in series_name:
                series = (
                    session.query(Series)
                        .filter(Series.name == my_series)
                        .one_or_none()
                )
                if series is not None:
                    log.debug(f"Series: {my_series} exists, skipped")
                else:
                    series = Series(name=my_series, description='')
                book.series.append(series)
            if series_id:
                book.series_id = int(series_id)
        session.add(book)
        session.commit()
        return True


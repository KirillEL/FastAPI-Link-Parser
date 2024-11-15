from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UrlList(Base):
    __tablename__ = 'urllist'
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)


class WordList(Base):
    __tablename__ = 'wordlist'
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False)


class WordLocation(Base):
    __tablename__ = 'wordlocation'
    id = Column(Integer, primary_key=True, index=True)
    fk_word_id = Column(Integer, ForeignKey('wordlist.id'), nullable=False)
    fk_url_id = Column(Integer, ForeignKey('urllist.id'), nullable=False)
    location = Column(Integer)


class LinkBetweenUrl(Base):
    __tablename__ = 'linkbetweenurl'
    id = Column(Integer, primary_key=True, index=True)
    fk_fromurl_id = Column(Integer, ForeignKey('urllist.id'), nullable=False)
    fk_tourl_id = Column(Integer, ForeignKey('urllist.id'), nullable=False)


class LinkWord(Base):
    __tablename__ = 'linkword'
    id = Column(Integer, primary_key=True, index=True)
    fk_word_id = Column(Integer, ForeignKey('wordlist.id'), nullable=False)
    fk_link_id = Column(Integer, ForeignKey('linkbetweenurl.id'), nullable=False)


class MatchRows(Base):
    __tablename__ = 'matchrows'

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey('urllist.id'), nullable=False)
    loc_word1 = Column(Integer, nullable=False)
    loc_word2 = Column(Integer, nullable=False)


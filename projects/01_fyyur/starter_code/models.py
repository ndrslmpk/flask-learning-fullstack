from datetime import datetime
import enum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ARRAY, DATE, JSON, Enum, MetaData

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


db = SQLAlchemy(metadata=metadata)
#----------------------------------------------------------------------------#
# Enums.
#----------------------------------------------------------------------------#

class Status(enum.Enum):
  searching = "Searching"
  booked = "Booked"

  def __str__(self):
    return self.name

  @classmethod
  def choices(cls):
    return [(choice, choice.value) for choice in cls]

  @classmethod
  def coerce(cls, item):
    return item if isinstance(item, Status) else Status[item]
  

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(JSON)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='Venue', lazy=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'Venue("{self.id}","{self.name}","{self.city}","{self.state}","{self.address}","{self.phone}","{self.genres}","{self.image_link}","{self.facebook_link}","{self.website_link}","{self.seeking_talent}","{self.seeking_description}", "{self.created_at}")'
    
    @property
    def serialize(self):
      """Return object data in easily serializable format"""
      return {
          'id'                      : self.id,
          'name'                    : self.name,
          'city'                    : self.city,
          'state'                   : self.state,
          'address'                 : self.address,
          'phone'                   : self.phone,
          'genres'                  : self.genres,
          'image_link'              : self.image_link,
          'facebook_link'           : self.facebook_link,
          'website_link'            : self.website_link,
          'seeking_talent'          : self.seeking_talent,
          'seeking_description'     : self.seeking_description,
          'shows'           	      : self.shows,
          'created_at'              : self.created_at,
      }

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(JSON) # genres might better be a nested object or an Array
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='Artist', lazy=True) # 1 <--Artist--[has-many]--Shows--> N
    availabilities = db.relationship('Availability', backref='Artist', lazy=True) # 1 <--Artist--[has-many]--Shows--> N
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # artist.upcoming_shows_count => Needs to be implemented in the Controller
    # artist.pasts_shows_count => Needs to be implented in the Controller
    
    def __repr__(self):
      return f'Artist( "{self.id}", "{self.name}", "{self.city}", "{self.state}", "{self.phone}", "{self.genres}", "{self.image_link}", "{self.facebook_link}", "{self.website_link}", "{self.seeking_venue}", "{self.seeking_description}", "{self.created_at}")'

    @property
    def serialize(self):
      """Return object data in easily serializable format"""
      return {
          'id'                      : self.id,
          'name'                    : self.name,
          'city'                    : self.city,
          'state'                   : self.state,
          'phone'                   : self.phone,
          'genres'                  : self.genres,
          'image_link'              : self.image_link,
          'facebook_link'           : self.facebook_link,
          'website_link'            : self.website_link,
          'seeking_venue'           : self.seeking_venue,
          'seeking_description'     : self.seeking_description,
          'shows'           	      : self.shows,
          'created_at'              : self.created_at,
          # 'modified_at': dump_datetime(self.modified_at),
          # This is an example how to deal with Many2Many relations
          #  'many2many'  : self.serialize_many2many
      }
    # @property
    # def serialize_many2many(self):
    #   """
    #   Return object's relations in easily serializable format.
    #   NB! Calls many2many's serialize property.
    #   """
    #   return [ item.serialize for item in self.many2many]


class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete='CASCADE'), nullable=False) # N <--Shows--[have-always-one]--Artist--> N
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', ondelete='CASCADE'), nullable=False)
  availability = db.relationship('Availability', backref='Show', lazy=True) # 1 <--Show--[has-many]--Availabilities--> N
  created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

  @property
  def serialize(self):
    """Return object data in easily serializable format"""
    return {
      'id'                      : self.id,
      'start_time'              : self.start_time,
      'artist_id'               : self.artist_id,
      'venue_id'                : self.venue_id,
      'created_at'              : self.created_at,
    }

class Availability(db.Model):
  __tablename__ = 'Availability'
  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete='CASCADE'), nullable=False) # N <--Availabilities--[have-always-one]--Artist--> N
  date = db.Column(db.Date)
  status = db.Column(db.Enum(Status)) 
  show_id = db.Column(db.Integer, db.ForeignKey('Show.id', ondelete='CASCADE'), nullable=True)
  created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

  @property
  def serialize(self):
    """Return object data in easily serializable format"""
    return {
      'id'                      : self.id,
      'artist_id'               : self.artist_id,
      'date'                    : self.date,
      'status'                  : self.status,
      'show_id'                 : self.show_id,
      'created_at'              : self.created_at,
    }

  def __repr__(self):
    return f'Availability("{self.id}","{self.artist_id}","{self.date}","{self.status}","{self.show_id}")'
    
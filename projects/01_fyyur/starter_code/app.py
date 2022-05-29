#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from enum import Enum
import json
from os import abort
import re
import sys
import dateutil.parser
import babel
from flask import Flask, jsonify, render_template, request, Response, flash, redirect, url_for
import sqlalchemy as sqla
from sqlalchemy import MetaData, inspect, ARRAY
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy.dialects.postgresql import JSON
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Enums
#----------------------------------------------------------------------------#

class Genres(Enum):
  alternative ='Alternative'
  blues ='Blues'
  classical = 'Classical'
  country = 'Country'
  electronic = 'Electronic'
  folk = 'Folk'
  funk = 'Funk'
  hiphop ='Hip-Hop'
  house = 'House'
  heavymetal = 'Heavy Metal'
  instrumental = 'Instrumental'
  jazz = 'Jazz'
  musicaltheatre = 'Musical Theatre'
  pop = 'Pop'
  punk = 'Punk'
  rnb = 'R&B'
  reggae = 'Reggae'
  rocknroll = 'Rock n Roll'
  soul = 'Soul'
  techno = 'Techno'
  other = 'Other'

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

    def __repr__(self):
        return f'Venue("{self.id}","{self.name}","{self.city}","{self.address}","{self.phone}","{self.genres}","{self.image_link}","{self.facebook_link}","{self.website_link}","{self.seeking_talent}","{self.seeking_description}")'
    
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
    # artist.upcoming_shows_count => Needs to be implemented in the Controller
    # artist.pasts_shows_count => Needs to be implented in the Controller
    
    def __repr__(self):
      return f'Artist("{self.id}","{self.name}","{self.city}","{self.state}","{self.phone}","{self.genres}","{self.image_link}","{self.facebook_link}","{self.website_link}","{self.seeking_venue}","{self.seeking_description}")'

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
          'seeking_venue'          : self.seeking_venue,
          'seeking_description'     : self.seeking_description,
          'shows'           	      : self.shows,
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
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False) # N <--Shows--[have-always-one]--Artist--> N
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = Venue.query.all()
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  param = request.form["search_term"]
  print("param", param)
  query = Venue.query.filter(Venue.name.ilike("%{}%".format(param))).all()
  print("query", query)
  if(len(query)==0):
    response = {
      "count": len(query),
      "data": []
      }
  else:
    data = [i.serialize for i in query]
    response = {
      "count": len(query),
      "data": data
      }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>', methods=['GET'])
def show_venue(venue_id):
  data = Venue.query.filter_by(id=venue_id).first_or_404()
  return render_template('pages/show_venue.html', venue=data)
  # TODO: Implement upcoming_shows and further missing data fields
  data3={
    "id": 3,
    "name": "Park Square Live Music & Coffee",
    "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
    "address": "34 Whiskey Moore Ave",
    "city": "San Francisco",
    "state": "CA",
    "phone": "415-000-1234",
    "website": "https://www.parksquarelivemusicandcoffee.com",
    "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
    "seeking_talent": False,
    "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    "past_shows": [{
      "artist_id": 5,
      "artist_name": "Matt Quevedo",
      "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
      "start_time": "2019-06-15T23:00:00.000Z"
    }],
    "upcoming_shows": [{
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-01T20:00:00.000Z"
    }, {
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-08T20:00:00.000Z"
    }, {
      "artist_id": 6,
      "artist_name": "The Wild Sax Band",
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": "2035-04-15T20:00:00.000Z"
    }],
    "past_shows_count": 1,
    "upcoming_shows_count": 1,
  }

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # temprorary store data as dict to store multiselect genres as list object
  dict = request.form.to_dict(flat=False)
  error = False
  try:
    # Get form data
    _name = request.form["name"] 
    _city = request.form["city"] 
    _state = request.form["state"] 
    _address = request.form["address"] 
    _phone = request.form["phone"] 
    _genres = dict["genres"] 
    _facebook_link = request.form["facebook_link"] 
    _image_link = request.form["image_link"] 
    _website_link = request.form["website_link"] 
    _seeking_talent = request.form.get("seeking_talent", False)
    if _seeking_talent == 'y': 
      _seeking_talent = True
    _seeking_description = request.form["seeking_description"] 

    # Create new Venue
    _venue = Venue(
      name = _name,
      city = _city,
      state = _state,
      address = _address,
      phone = _phone,
      genres = _genres,
      facebook_link = _facebook_link,
      image_link = _image_link,
      website_link = _website_link,
      seeking_talent = _seeking_talent,
      seeking_description = _seeking_description 
    )
    db.session.add(_venue)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    abort()
    

  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error=True
  try:
    _venue = Venue.query.filter(Venue.id == venue_id).delete()
    print(_venue)
    db.session.commit()
  except Exception as e:
        print(e)
        error = True
        db.session.rollback()
  finally:
      db.session.close()
      if not error:
          flash('Venue was successfully deleted!')
          return render_template('pages/home.html')
      else:
          flash('An error occurred. Venue could not be deleted.')
      return None

  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # 

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  param = request.form["search_term"]
  query = Artist.query.filter(Artist.name.ilike("%{}%".format(param))).all()
  if(len(query)==0):
    response = {
      "count": len(query),
      "data": []
      }
  else:
    data = [i.serialize for i in query]
    response = {
      "count": len(query),
      "data": data
      }
    print(response)
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data = Artist.query.filter_by(id=artist_id).first_or_404()
  return render_template('pages/show_artist.html', artist=data)

  data2={
    "id": 5,
    "name": "Matt Quevedo",
    "genres": ["Jazz"],
    "city": "New York",
    "state": "NY",
    "phone": "300-400-5000",
    "facebook_link": "https://www.facebook.com/mattquevedo923251523",
    "seeking_venue": False,
    "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "past_shows": [{
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2019-06-15T23:00:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }
  data3={
    "id": 6,
    "name": "The Wild Sax Band",
    "genres": ["Jazz", "Classical"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "432-325-5432",
    "seeking_venue": False,
    "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "past_shows": [],
    "upcoming_shows": [{
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-01T20:00:00.000Z"
    }, {
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-08T20:00:00.000Z"
    }, {
      "venue_id": 3,
      "venue_name": "Park Square Live Music & Coffee",
      "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
      "start_time": "2035-04-15T20:00:00.000Z"
    }],
    "past_shows_count": 0,
    "upcoming_shows_count": 3,
  }

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(request.POST, obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)
  _data = request.form
  form = ArtistForm(formdata=_data, obj=artist)
  if request.POST and form.validate():
    form.populate_obj(artist)
    artist.save()
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  _data = request.form
  form = VenueForm(formdata=_data, obj=venue)
  if request.POST and form.validate():
    form.populate_obj(venue)
    venue.save()
  if request.POST:
    data = request.form 
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # temprorary store data as dict to store multiselect genres as list object
  dict = request.form.to_dict(flat=False)
  error = False
  try:
    # Get form data
    _name = request.form["name"] 
    _city = request.form["city"] 
    _state = request.form["state"] 
    _phone = request.form["phone"] 
    _genres = dict["genres"] 
    _facebook_link = request.form["facebook_link"] 
    _image_link = request.form["image_link"] 
    _website_link = request.form["website_link"] 
    _seeking_venue = request.form.get("seeking_venue", False)
    if _seeking_venue == 'y': 
      _seeking_venue = True
    _seeking_description = request.form["seeking_description"] 

    # Create new Artist
    _artist = Artist(
      name = _name,
      city = _city,
      state = _state,
      phone = _phone,
      genres = _genres,
      facebook_link = _facebook_link,
      image_link = _image_link,
      website_link = _website_link,
      seeking_venue = _seeking_venue,
      seeking_description = _seeking_description 
    )
    db.session.add(_artist)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.', 'error')
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    abort()

  # on successful db insert, flash success
  flash('Artist ' + request.form['name'] + ' was successfully listed!', )
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., 
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-01T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-08T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-15T20:00:00.000Z"
  }]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error=False
  # Get form data
  print(request.form["artist_id"])
  print(request.form["venue_id"])
  print(request.form["start_time"])
  try:
    _artist_id = request.form["artist_id"] 
    _venue_id = request.form["venue_id"] 
    _start_time = request.form["start_time"] 

  # Create new Venue
    _show = Show(
      artist_id = _artist_id,
      venue_id = _venue_id,
      start_time = _start_time
    )
    db.session.add(_show)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    abort()
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

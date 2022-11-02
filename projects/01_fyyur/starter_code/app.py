#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from collections import namedtuple
from http.client import HTTPException
import json
import logging
import re
import string
import sys
from datetime import date, time
from enum import Enum
from logging import FileHandler, Formatter
from sre_parse import State

import babel
import dateutil.parser
import sqlalchemy as sqla
import sqlalchemy.dialects.postgresql as pg
from flask import (Flask, Response, flash, jsonify, redirect, render_template,
                   request, url_for, abort)
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from psycopg2 import Time
from sqlalchemy import ARRAY, Date, MetaData, inspect, null
from sqlalchemy.dialects.postgresql import JSON

from forms import *
from models import db, Venue, Artist, Show, Availability, Status


#----------------------------------------------------------------------------#
# App Config. (Factory Pattern)
#----------------------------------------------------------------------------#



def create_app():
  app = Flask(__name__)
  moment = Moment(app)
  app.config.from_object('config')
  # app.debug = True
  
  db.init_app(app)
  migrate = Migrate(app, db)

  return app

app = create_app()

if __name__ == "__main__":
  db.create_all()
  app.debug = True
  app.run()

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
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else:
    date=value
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
  venues = Venue.query.order_by(Venue.created_at.desc()).limit(10).all()
  print(venues)
  artists = Artist.query.order_by(Artist.created_at.desc()).limit(10).all()
  print(artists)
  # PredefinedData = namedtuple('data', ['artist', 'venue'])
  # predefined_data = PredefinedData(artist_id)


  return render_template('pages/home.html', artists=artists, venues=venues)

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  response = []

  areas = Venue.query.with_entities(Venue.state, Venue.city).distinct().all() # returns all existing combinations of "state" and "city" for venues 
  for area in areas:
    entries = Venue.query.filter_by(state=area.state, city=area.city).all()
    entity = {
      "city": area.city,
      "state": area.state,
      "venues": [{"id": v.id, "name": v.name, "num_upcoming_shows": v.shows} for v in entries]
    }
    response.append(entity)
  data = response
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  param = request.form["search_term"]
  query = Venue.query.filter(Venue.name.ilike("%{}%".format(param)) | Venue.city.ilike("%{}%".format(param)) | Venue.state.ilike("%{}%".format(param))).all()
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
  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  shows = Show.query.filter_by(venue_id=venue_id).all()
  upcoming_shows = []
  past_shows = []
  for show in shows:
    artist = Artist.query.filter_by(id=show.artist_id).first_or_404()
    if(show.start_time >= datetime.now()):
      upcoming_shows.append({
        "artist_id": artist.id, 
        "artist_name":artist.name, 
        "artist_image_link": artist.image_link,
        "start_time": show.start_time
        })
    elif(show.start_time < datetime.now()):
      past_shows.append({
        "artist_id": artist.id, 
        "artist_name":artist.name, 
        "artist_image_link": artist.image_link,
        "start_time": show.start_time
        })
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "genres": venue.genres,
    "image_link": venue.image_link,
    "facebook_link": venue.facebook_link,
    "website_link": venue.website_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_venue.html', venue=data)

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
    abort(500)
    flash('ERROR: An error occurred. Show could not be listed.', 'error')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

@app.route('/venues/delete/<int:venue_id>', methods=['POST'])
def delete_venue(venue_id):
  error=False
  try:
    _venue = Venue.query.filter_by(id=venue_id).first_or_404()
    db.session.delete(_venue)
    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error==False:
    flash('Venue was successfully deleted!')
  else:
    flash('An error occurred. Venue could not be deleted.')
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  param = request.form["search_term"]
  query = Artist.query.filter(Artist.name.ilike("%{}%".format(param)) | Artist.state.ilike("%{}%".format(param)) | Artist.city.ilike("%{}%".format(param))).all()
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
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  shows = Show.query.filter_by(artist_id=artist_id).all()
  availabilities = Availability.query.filter_by(artist_id=artist_id).all()
  upcoming_shows = []
  past_shows = []
  for show in shows:
    venue = Venue.query.filter_by(id=show.venue_id).first_or_404()
    if(show.start_time >= datetime.now()):
      upcoming_shows.append({
        "venue_id": venue.id, 
        "venue_name":venue.name, 
        "venue_image_link": venue.image_link,
        "start_time": show.start_time
        })
    elif(show.start_time < datetime.now()):
      past_shows.append({
        "venue_id": venue.id, 
        "venue_name":venue.name, 
        "venue_image_link": venue.image_link,
        "start_time": show.start_time
        })
  print("availabilities")
  print(availabilities)
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "genres": artist.genres,
    "image_link": artist.image_link,
    "facebook_link": artist.facebook_link,
    "website_link": artist.website_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
    "availabilities": availabilities,
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  print(artist.availabilities)
  artist = artist.serialize
  # print(artist.serialize)
  form = ArtistForm(data=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error=False
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  dict_format = request.form.to_dict(flat=False)
  try:
    # Get form data
    _name = request.form["name"] 
    _city = request.form["city"] 
    _state = request.form["state"] 
    _phone = request.form["phone"] 
    _genres = dict_format["genres"] 
    _facebook_link = request.form["facebook_link"] 
    _image_link = request.form["image_link"] 
    _website_link = request.form["website_link"] 
    _seeking_venue = request.form.get("seeking_venue", False)
    if _seeking_venue == 'y': 
      _seeking_venue = True
    _seeking_description = request.form["seeking_description"] 
    # Update Artist
    artist.name = _name
    artist.city = _city
    artist.state = _state
    artist.phone = _phone
    artist.genres = _genres
    artist.facebook_link = _facebook_link
    artist.image_link = _image_link
    artist.website_link = _website_link
    artist.seeking_venue = _seeking_venue
    artist.seeking_description = _seeking_description
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Artist could not be updated.', 'error')
  finally:
    db.session.close()
  if error==True:
    flash('ERROR: Artist was not listed!', )
  else: 
    flash('Artist ' + request.form['name'] + ' was successfully updated!', )
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  venue = venue.serialize
  form = VenueForm(data=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error=False
  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  dict_format = request.form.to_dict(flat=False)
  try:
    # Get form data
    _name = request.form["name"] 
    _city = request.form["city"] 
    _address = request.form["address"] 
    _state = request.form["state"] 
    _phone = request.form["phone"]
    _genres = dict_format["genres"]
    _facebook_link = request.form["facebook_link"] 
    _image_link = request.form["image_link"] 
    _website_link = request.form["website_link"] 
    _seeking_talent = request.form.get("seeking_talent", False)
    if _seeking_talent == 'y': 
      _seeking_talent = True
    _seeking_description = request.form["seeking_description"] 
    # Update Venue
    venue.name = _name
    venue.city = _city
    venue.address = _address
    venue.state = _state
    venue.phone = _phone
    venue.genres = _genres
    venue.facebook_link = _facebook_link
    venue.image_link = _image_link
    venue.website_link = _website_link
    venue.seeking_talent = _seeking_talent
    venue.seeking_description = _seeking_description
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error==True:
    flash('ERROR:Venue could not be updated.', 'error')
  else: 
    flash('Venue ' + request.form['name'] + ' was successfully updated!', )

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
    _availabilities = request.form["availabilities"] 

    if not _availabilities:
      # Set today as default availability if none is chosen
      availability_dates = None
    else:
      # if availabilities as Array are given, convert them into datetime objects
      print("_availabilities")
      print(_availabilities)
      print(type(_availabilities))
      availability_dates = _availabilities.split(",")

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

    if availability_dates is not None:
      for date in availability_dates:
        # check if date can be converted into a valid date
        converted_date = datetime.strptime(date,'%m/%d/%Y').date()
        _availability = Availability(
          artist_id = _artist,
          date = converted_date,
          status = Status.searching,
          show_id = None
        )
        _artist.availabilities.append(_availability)
    db.session.add(_artist)
    db.session.commit()
  except Exception as e:
    print(e)
    print("Error occured")
    error=True
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.', 'error')
  finally:
    db.session.close()
  if error:
    abort(500)
    flash('ERROR: Artist was not listed!', 'error')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []
  query_show = Show.query.join(Artist).join(Venue).with_entities(Venue.id, Venue.name, Artist.id, Artist.name, Artist.image_link, Show.start_time).all()
  for row in query_show:
    # Takes each column[i] of a returned query object and assigns it
    show_data = {
      "venue_id": row[0],
      "venue_name": row[1],
      "artist_id": row[2],
      "artist_name": row[3],
      "artist_image_link": row[4],
      "start_time": row[5]
    }
    data.append(show_data)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error=False
  try:
    _artist_id = request.form["artist_id"] 
    _venue_id = request.form["venue_id"] 
    _start_time = request.form["start_time"] 
    
    # Prevent the creation of Shows on the same 
    # TODO: Implement logic that just recognizes availabilites that are booked
    date = datetime.strptime(_start_time, '%Y-%m-%d %H:%M:%S').date()
    availabilities = Availability.query.filter_by(artist_id=_artist_id).all()
    for a in availabilities:
      if date == a.date:
        flash('The given Start Time is already booked. Please choose another starting Date.', 'error')
        db.session.rollback()
        return render_template('pages/home.html')

  # Create new Venue
    _show = Show(
      artist_id = _artist_id,
      venue_id = _venue_id,
      start_time = _start_time
    )
    # TODO: Set the given availability to being booked.
    db.session.add(_show)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    abort(404)
    flash('ERROR: An error occurred. Show could not be listed.', 'error')
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

# Availabilities
#----------------------------------------------------------------------------#

@app.route('/artists/<int:artist_id>/availabilities/create', methods=['GET'])
def create_availability_form(artist_id):
  PredefinedData = namedtuple('predefineddata', ['artist_id'])
  predefined_data = PredefinedData(artist_id)
  form = AvailabilityForm(obj=predefined_data)
  return render_template('forms/new_availability.html', form=form)

@app.route('/artists/<int:artist_id>/availabilities/create', methods=['POST'])
def create_artist_availability(artist_id):
  # temporary store data as dict to store multiselect genres as list object
  dict = request.form.to_dict(flat=False)

  error = False
  try:
    _artist_id = artist_id
    _date = request.form["date"]
    _status = request.form["status"]
    if request.form["show_id"] == '':
      _show_id = None
    else: 
      _show_id = request.form["show_id"]

    print(_date)
    converted_date = datetime.strptime(_date,'%Y-%m-%d').date()

    _availability = Availability(
      artist_id = _artist_id,
      date = converted_date,
      status = _status,
      show_id = _show_id,
    )

    db.session.add(_availability)
    db.session.commit()
  except Exception as e:
    print(e)
    print("Error occured")
    error=True
    db.session.rollback()
    flash('An error occurred. Artist ' + str(artist_id) + ' could not be listed.', 'error')
  finally:
    db.session.close()
  if error:
    abort(500)
    flash('ERROR: Artist was not listed!', 'error')
  else:
    flash("Artist's availability" + str(artist_id) + "was successfully listed!")

  return render_template('pages/home.html')

@app.route('/artists/<int:artist_id>/availabilities/<int:availability_id>/edit', methods=['GET'])
def edit_availability_form(artist_id, availability_id):
  availability = Availability.query.filter_by(id=availability_id).first_or_404()

  availability = availability.serialize

  form = AvailabilityForm(data=availability)
  return render_template('forms/new_availability.html', form=form)

@app.route('/artists/<int:artist_id>/availabilities/delete/<int:availability_id>', methods=['POST'])
def delete_availability(artist_id, availability_id):
  error=False
  try:
    _availability = Availability.query.filter_by(id=availability_id).first_or_404()
    db.session.delete(_availability)
    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error==False:
    flash('Availability was successfully deleted!')
  else:
    flash('An error occurred. Availability could not be deleted.')
  return render_template('pages/home.html')

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

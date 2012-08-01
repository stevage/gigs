from django import template
from django import forms
from django.db.models.query import QuerySet
from gmapi.forms.widgets import GoogleMap
from gmapi import maps

from gigs.gig_registry.models import Location, Gig, Venue, Band


class MapForm(forms.Form):
    map = forms.Field(widget=GoogleMap(attrs={'width':510, 'height':510}))


class MapNode(template.Node):
    
    def __init__(self, locatables):
        self.locatables = template.Variable(locatables)
        self.lat = -37.809018
        self.lon = 144.963635
        self.gmap = maps.Map(opts = {
            'center': maps.LatLng(self.lat, self.lon),
            'mapTypeId': maps.MapTypeId.ROADMAP,
            'zoom': 8,
            'mapTypeControlOptions': {
            'style': maps.MapTypeControlStyle.DROPDOWN_MENU
                },
            })
   
    def render(self, context):
        try:
            locatables = self.locatables.resolve(context)
        except template.VariableDoesNotExist:
            return ''
        
        if isinstance(locatables, QuerySet):
            cls = locatables.model
        else:
            try:
                cls = locatables.__class__
                if cls == Location:
                    locatables = [locatables]
            except AttributeError:
                return ''

        funcs = {
                Gig: Location.objects.for_gigs,
                Venue: Location.objects.for_venues,
                Band: Location.objects.for_bands,
                }
        try:
            func = funcs[cls]
            locations = func(locatables)
        except KeyError:
            if cls == Location:
                locations = locatables
            else:
                return ''


        for location in locations:
            lat = location.lat
            lon = location.lon
            marker = maps.Marker(opts = {
                'map': self.gmap,
                'position': maps.LatLng(lat, lon),
                })
        context['form'] = MapForm(initial={'map': self.gmap})
        return ''

class GigSearchMapNode(MapNode):
    
    def render(self, context):
        try:
            locatables = self.locatables.resolve(context)
        except template.VariableDoesNotExist:
            return ''
        
        
        for gig_search_result in locatables:
            gig = gig_search_result.object
            if gig.venue and  gig.venue.location:
                lat = gig.venue.location.lat
                lon = gig.venue.location.lon
                marker = maps.Marker(opts = {
                    'map': self.gmap,
                    'position': maps.LatLng(lat, lon),
                    })
                info = maps.InfoWindow({
                            'content': "gig location",
                            'disableAutoPan': True
                                        })
                info.open(self.gmap, marker)
                context['form'] = MapForm(initial={'map':self.gmap})
        return ''

def do_map(parser, token):
    
    try:
        tag_name, instances = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('%r tag requires 2 arguments' % 
                token.contents.split()[0])
    if tag_name == "search_map":
        return GigSearchMapNode(instances)
    return MapNode(instances)

register = template.Library()
register.tag('map', do_map)
register.tag('search_map', do_map)
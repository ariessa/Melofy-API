# Import Flask library
import flask
import magenta
import note_seq
import urllib.request
import tensorflow

from flask import request

# Import dependencies for Magenta
from magenta.models.melody_rnn import melody_rnn_sequence_generator
from magenta.models.shared import sequence_generator_bundle
from note_seq.protobuf import generator_pb2
from note_seq.protobuf import music_pb2

# Create a Flask application object
app = flask.Flask(__name__)

# Start the debugger
app.config["DEBUG"] = True

# A route to return the homepage
@app.route('/', methods=['GET'])
def home():
    return '''<h1>Generate Melody API</h1>
<p>An API for generating melody from supplied audio file link.</p>'''

# A route to 404 page
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

# A route to generate melody from supplied audio file link
@app.route('/generate', methods=['POST'])
def generate_melody():
    # If there is no request data in json or audio_file item in request data
    # Abort the request and return error code 400
    if not request.json or not 'audio_file_link' in request.json:
        abort(400)

    # Retrieve audio file link from request.json
    audio_file_link = request.json['audio_file_link']

    # Download audio file from audio_file_link
    print('Beginning file download with urllib2...')

    url = 'https://drive.google.com/file/d/17WUeEsZZ8L-inC4uFXz5Kv6nehmwN2FN/view?usp=sharing'
    urllib.request.urlretrieve(url, '/Users/aries/Downloads/test.wav')


    # # Convert audio file from WAV to MIDI
    # converted_audio_file = ""

    # # Convert audio file from MIDI to Note Sequence
    # test = note_seq.midi_file_to_note_sequence('/content/twinkle_twinkle_little_star.mid')

    # # Initialize the model
    # print("Initializing Melody RNN...")
    # bundle = sequence_generator_bundle.read_bundle_file('/content/basic_rnn.mag')
    # generator_map = melody_rnn_sequence_generator.get_generator_map()
    # melody_rnn = generator_map['basic_rnn'](checkpoint=None, bundle=bundle)
    # melody_rnn.initialize()
    # print('🎉 Done!')

    # # Model options. Change these to get different generated sequences! 
    # input_sequence = converted_audio_file 
    # num_steps = 128 # change this for shorter or longer sequences
    # temperature = 1.0 # the higher the temperature the more random the sequence.

    # # Set the start time to begin on the next step after the last note ends.
    # last_end_time = (max(n.end_time for n in input_sequence.notes)
    #                 if input_sequence.notes else 0)
    # qpm = input_sequence.tempos[0].qpm 
    # seconds_per_step = 60.0 / qpm / melody_rnn.steps_per_quarter
    # total_seconds = num_steps * seconds_per_step

    # generator_options = generator_pb2.GeneratorOptions()
    # generator_options.args['temperature'].float_value = temperature
    # generate_section = generator_options.generate_sections.add(
    # start_time=last_end_time + seconds_per_step,
    # end_time=total_seconds)

    # # Ask the model to continue the sequence.
    # sequence = melody_rnn.generate(input_sequence, generator_options)

    # # note_seq.plot_sequence(sequence)
    # note_seq.play_sequence(sequence, synth=note_seq.fluidsynth)

    # # Assign link to download generated melody
    # # Link will be available for download
    # # After 1 hour, link will be deleted
    # link = ""

    # return "Generated Melody: " + link
    return "It works 🎉!\n\n" + audio_file_link

# Run the application server
app.run()

# Example of correct POST request
# curl -i -X POST -H "Content-Type:application/json" -d "{\"audio_file_link\": \"https://drive.google.com/file/d/17WUeEsZZ8L-inC4uFXz5Kv6nehmwN2FN/view?usp=sharing\" }" http://localhost:5000/api/v1/generate
# curl -i -X POST -F "file=@twinkle_twinkle_little_star.wav" http://localhost:5000/api/v1/generate
################################################################################
# The MIT License
#
# Copyright (c) 2021-2023, Prominence AI, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
################################################################################

################################################################################
#
# This example demonstrates the use of two ODE Instance Triggers -- one for 
# the Person class and the other for the Vehicle class -- to trigger on new 
# Object instances as identified by an IOU Tracker. A Print Action is added 
# to the Instance Triggers to print out the event data for each new object. 
#  
# The example uses a basic inference Pipeline consisting of:
#   - A URI Source
#   - Primary GST Inference Engine (PGIE)
#   - IOU Tracker
#   - On-Screen Display
#   - Window Sink
#  
################################################################################

#!/usr/bin/env python

import sys
sys.path.insert(0, "../../")
from dsl import *

uri_h265 = "/opt/nvidia/deepstream/deepstream/samples/streams/sample_1080p_h265.mp4"

# Filespecs for the Primary GIE
primary_infer_config_file = \
    '/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_infer_primary.txt'
primary_model_engine_file = \
    '/opt/nvidia/deepstream/deepstream/samples/models/Primary_Detector/resnet18_trafficcamnet.etlt_b8_gpu0_int8.engine'

# Filespec for the IOU Tracker config file
iou_tracker_config_file = \
    '/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_tracker_IOU.yml'

PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3

TILER_WIDTH = DSL_1K_HD_WIDTH
TILER_HEIGHT = DSL_1K_HD_HEIGHT
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

## 
# Function to be called on XWindow KeyRelease event
## 
def xwindow_key_event_handler(key_string, client_data):
    print('key released = ', key_string)
    if key_string.upper() == 'P':
        dsl_pipeline_pause('pipeline')
    elif key_string.upper() == 'R':
        dsl_pipeline_play('pipeline')
    elif key_string.upper() == 'Q' or key_string == '' or key_string == '':
        dsl_pipeline_stop('pipeline')
        dsl_main_loop_quit()
 
## 
# Function to be called on XWindow Delete event
## 
def xwindow_delete_event_handler(client_data):
    print('delete window event')
    dsl_pipeline_stop('pipeline')
    dsl_main_loop_quit()

## 
# Function to be called on End-of-Stream (EOS) event
## 
def eos_event_listener(client_data):
    print('Pipeline EOS event')
    dsl_pipeline_stop('pipeline')
    dsl_main_loop_quit()

## 
# Function to be called on every change of Pipeline state
## 
def state_change_listener(old_state, new_state, client_data):
    print('previous state = ', old_state, ', new state = ', new_state)
    if new_state == DSL_STATE_PLAYING:
        dsl_pipeline_dump_to_dot('pipeline', "state-playing")

def main(args):

    # Since we're not using args, we can Let DSL initialize GST on first call
    while True:
            
        #`````````````````````````````````````````````````````````````````````````````
        # Create a Format Label Action to remove the Object Label from view
        # Note: the label can be disabled with the OSD API as well. 
        retval = dsl_ode_action_label_format_new('remove-label', 
            font=None, has_bg_color=False, bg_color=None)
        if retval != DSL_RETURN_SUCCESS:
            break
            
        # Create a Format Bounding Box Action to remove the box border from view
        retval = dsl_ode_action_bbox_format_new('remove-border', border_width=0,
            border_color=None, has_bg_color=False, bg_color=None)
        if retval != DSL_RETURN_SUCCESS:
            break

        # Create an Any-Class Occurrence Trigger for our Hide Action
        retval = dsl_ode_trigger_occurrence_new('every-occurrence-trigger', 
            source='uri-source-1', class_id=DSL_ODE_ANY_CLASS, 
            limit=DSL_ODE_TRIGGER_LIMIT_NONE)
        if retval != DSL_RETURN_SUCCESS:
            break
        retval = dsl_ode_trigger_action_add_many('every-occurrence-trigger', 
            actions=['remove-label', 'remove-border', None])
        if retval != DSL_RETURN_SUCCESS:
            break

            
        # And a single action to print the event data to the console, which will be used
        # by both our PERSON and VEHICLE Instance Trigers - created next
        retval = dsl_ode_action_print_new('print-data', force_flush=False)
        if retval != DSL_RETURN_SUCCESS:
            break

        #`````````````````````````````````````````````````````````````````````````````
        # Create two new Instance triggers, one for the PERSON class, the other 
        # for the VEHICLE class.
        retval = dsl_ode_trigger_instance_new('person-instance-trigger', 
            source='uri-source-1', class_id=PGIE_CLASS_ID_PERSON, 
            limit=DSL_ODE_TRIGGER_LIMIT_NONE)
        if retval != DSL_RETURN_SUCCESS:
            break

        retval = dsl_ode_trigger_instance_new('vehicle-instance-trigger', 
            source='uri-source-1', class_id=PGIE_CLASS_ID_VEHICLE, 
            limit=DSL_ODE_TRIGGER_LIMIT_NONE)
        if retval != DSL_RETURN_SUCCESS:
            break

        # Override the default behavior of the instance triggers to trigger for 
        # 10 consecutive ODE occurrences... suppression-count=0 (defualt) means 
        # suppress indefinitely once the instance-count has been reached. 
        retval = dsl_ode_trigger_instance_count_settings_set('person-instance-trigger', 
            instance_count=10, suppression_count=0)

        retval = dsl_ode_trigger_instance_count_settings_set('person-instance-trigger', 
            instance_count=10, suppression_count=0)

        #`````````````````````````````````````````````````````````````````````````````
        # Next, we add our Actions to our Triggers
        retval = dsl_ode_trigger_action_add('person-instance-trigger', 'print-data')
        if retval != DSL_RETURN_SUCCESS:
            break
        retval = dsl_ode_trigger_action_add('vehicle-instance-trigger', 'print-data')
        if retval != DSL_RETURN_SUCCESS:
            break

        #`````````````````````````````````````````````````````````````````````````````
        # New ODE Handler to handle all ODE Triggers    
        retval = dsl_pph_ode_new('ode-handler')
        if retval != DSL_RETURN_SUCCESS:
            break
        retval = dsl_pph_ode_trigger_add_many('ode-handler', 
            triggers=['every-occurrence-trigger', 'person-instance-trigger', 
            'vehicle-instance-trigger', None])
        if retval != DSL_RETURN_SUCCESS:
            break
        
        ##############################################################################
        #
        # Create the remaining Pipeline components
        
        # New URI File Source using the filespec defined above
        retval = dsl_source_uri_new('uri-source-1', uri_h265, False, False, 0)
        if retval != DSL_RETURN_SUCCESS:
            break

        # New Primary GIE using the filespecs above with interval = 0
        retval = dsl_infer_gie_primary_new('primary-gie', 
            primary_infer_config_file, primary_model_engine_file, 1)
        if retval != DSL_RETURN_SUCCESS:
            break

        # New IOU Tracker, setting operational width and hieght
        retval = dsl_tracker_new('iou-tracker', iou_tracker_config_file, 480, 272)
        if retval != DSL_RETURN_SUCCESS:
            break

        # New OSD with text, clock and bbox display all enabled. 
        retval = dsl_osd_new('on-screen-display', 
            text_enabled=True, clock_enabled=True, 
            bbox_enabled=True, mask_enabled=False)
        if retval != DSL_RETURN_SUCCESS:
            break

        # Add our ODE Pad Probe Handler to the source pad of the Tracker
        retval = dsl_osd_pph_add('on-screen-display', 
            handler='ode-handler', pad=DSL_PAD_SRC)
        if retval != DSL_RETURN_SUCCESS:
            break

        # New Window Sink, 0 x/y offsets and dimensions definded
        retval = dsl_sink_window_egl_new('egl-sink', 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        if retval != DSL_RETURN_SUCCESS:
            break

        # Add the XWindow event handler functions defined above to the Window Sink
        retval = dsl_sink_window_key_event_handler_add('egl-sink', 
            xwindow_key_event_handler, None)
        if retval != DSL_RETURN_SUCCESS:
            break
        retval = dsl_sink_window_delete_event_handler_add('egl-sink', 
            xwindow_delete_event_handler, None)
        if retval != DSL_RETURN_SUCCESS:
            break

        # Add all the components to our pipeline
        retval = dsl_pipeline_new_component_add_many('pipeline', 
            ['uri-source-1', 'primary-gie', 'iou-tracker', 
            'on-screen-display', 'egl-sink', None])
        if retval != DSL_RETURN_SUCCESS:
            break

        ## Add the listener callback functions defined above
        retval = dsl_pipeline_state_change_listener_add('pipeline', 
            state_change_listener, None)
        if retval != DSL_RETURN_SUCCESS:
            break
        retval = dsl_pipeline_eos_listener_add('pipeline', 
            eos_event_listener, None)
        if retval != DSL_RETURN_SUCCESS:
            break

        # Play the pipeline
        retval = dsl_pipeline_play('pipeline')
        if retval != DSL_RETURN_SUCCESS:
            break

        dsl_main_loop_run()
        retval = DSL_RETURN_SUCCESS
        break

    # Print out the final result
    print(dsl_return_value_to_string(retval))

    # Cleanup all DSL/GST resources
    dsl_delete_all()
    
if __name__ == '__main__':
    sys.exit(main(sys.argv))
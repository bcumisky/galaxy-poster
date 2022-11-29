import json
import logging

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import tensorflow as tf
import tensorflow_probability as tfp
from PIL import Image

def main(df):
    interactive_galaxies(df)


def interactive_galaxies(df):
    questions = {
        'bar': ['strong', 'weak', 'no'], 
        'has-spiral-arms': ['yes', 'no'],
        'spiral-arm-count': ['1', '2', '3', '4'],
        'spiral-winding': ['tight', 'medium', 'loose'],
        'merging': ['merger', 'major-disturbance', 'minor-disturbance', 'none']
    }
    # could make merging yes/no

    # st.sidebar.markdown('# Show posteriors')
    # show_posteriors = st.sidebar.selectbox('Posteriors for which question?', ['none'] + list(questions.keys()), format_func=lambda x: x.replace('-', ' ').capitalize())

    st.sidebar.markdown('# Choose Your Galaxies')
    # st.sidebar.markdown('---')
    current_selection = {}
    for question, answers in questions.items():
        valid_to_select = True
        st.sidebar.markdown("# " + question.replace('-', ' ').capitalize() + '?')

        # control valid_to_select depending on if question is relevant
        if question.startswith('spiral-'):
            has_spiral_answer, has_spiral_mean = current_selection.get('has-spiral-arms', [None, None])
            # logging.info(f'has_spiral limits: {has_spiral_mean}')
            if has_spiral_answer == 'yes':
                valid_to_select = np.min(has_spiral_mean) > 0.5
            else:
                valid_to_select = np.min(has_spiral_mean) < 0.5

        if valid_to_select:
            selected_answer = st.sidebar.selectbox('Answer', answers, format_func=lambda x: x.replace('-',' ').capitalize(), key=question+'_select')
            selected_mean = st.sidebar.slider(
                label='Posterior Mean',
                value=[.0, 1.],
                key=question+'_mean')
            current_selection[question] = (selected_answer, selected_mean)
            # and sort by confidence, for now
        else:
            st.sidebar.markdown('*To use this filter, set "Has Spiral Arms = Yes"to > 0.5*'.format(question))
            current_selection[question] = None, None

    galaxies = df
    logging.info('Total galaxies: {}'.format(len(galaxies)))
    valid = np.ones(len(df)).astype(bool)
    for question, answers in questions.items():
        answer, mean = current_selection.get(question, [None, None])  # mean is (min, max) limits
        logging.info(f'Current: {question}, {answer}, {mean}')
        if mean == None:  # happens when spiral count question not relevant
            mean = (None, None)
        if len(mean) == 1:
            # streamlit sharing bug is giving only the higher value
            logging.info('Streamlit bug is happening, working')
            mean = (0., mean[0])
        # st.markdown('{} {} {} {}'.format(question, answers, answer, mean))
        if (answer is not None) and (mean is not None):
            # this_answer = galaxies[question + '_' + answer + '_concentration_mean']
            # all_answers = galaxies[[question + '_' + a + '_concentration_mean' for a in answers]].sum(axis=1)
            this_answer = galaxies[question + '_' + answer + '_fraction']
            all_answers = galaxies[[question + '_' + a + '_fraction' for a in answers]].sum(axis=1)
            prob = this_answer / all_answers
            within_limits = (np.min(mean) <= prob) & (prob <= np.max(mean))

            preceding = True
            if mean != (0., 1.):
                preceding = galaxies[question + '_proportion_volunteers_asked'] >= 0.5

            logging.info('Fraction of galaxies within limits: {}'.format(within_limits.mean()))
            valid = valid & within_limits & preceding

    logging.info('Valid galaxies: {}'.format(valid.sum()))
    st.markdown('{:,} of {:,} galaxies match your criteria.'.format(valid.sum(), len(valid)))

    # selected = galaxies[valid].sample(np.min([valid.sum(), 16]))


    # image_locs = [row['file_loc'].replace('/decals/png_native', '/galaxy_zoo/gz2') for _, row in selected.iterrows()]
    # images = [np.array(Image.open(loc)).astype(np.uint8) for loc in image_locs]

    # if show_posteriors is not 'none':
    #     selected = galaxies[valid][:8]
    #     question = show_posteriors
    #     if question == 'spiral-count' or question == 'spiral-winding':
    #         st.markdown('Sorry! You asked to see posteriors for "{}", but this demo app only supports visualing posteriors for questions with two answers. Please choose another option.'.format(question.capitalize().replace('-', ' ')))
    #     else:
    #         answers = questions[question]
    #         selected_answer = current_selection[question][0]
    #         for _, galaxy in selected.iterrows():
    #             show_predictions(galaxy, question, answers, selected_answer)
    # else:
    # image_urls = ["https://panoptes-uploads.zooniverse.org/production/subject_location/02a32231-11c6-45b6-b448-fd85ec32fbd8.png"] * 16
    selected = galaxies[valid][:40]
    image_urls = selected['url']

    opening_html = '<div style=display:flex;flex-wrap:wrap>'
    closing_html = '</div>'
    child_html = ['<img src="{}" style=margin:3px;width:200px;></img>'.format(url) for url in image_urls]

    gallery_html = opening_html
    for child in child_html:
        gallery_html += child
    gallery_html += closing_html

    # st.markdown(gallery_html)
    st.markdown(gallery_html, unsafe_allow_html=True)
    # st.markdown('<img src="{}"></img>'.format(child_html), unsafe_allow_html=True)
    # for image in images:
    #     st.image(image, width=250)



    

# def show_predictions(galaxy, question, answers, answer): 

#     answer_index = answers.index(answer) 
#     # st.markdown(answer_index)

#     fig, (ax0, ax1) = plt.subplots(nrows=1, ncols=2, figsize=(10, 3 * 1))

#     total_votes = np.array(galaxy[question + '_total-votes']).astype(np.float32)  # TODO
#     votes = np.linspace(0., total_votes)
#     x = np.stack([votes, total_votes-votes], axis=-1)  # also need the counts for other answer, no
#     votes_this_answer = x[:, answer_index]

#     cycler = mpl.rcParams['axes.prop_cycle']
#     # https://matplotlib.org/cycler/
#     colors = [c['color'] for c in cycler]

#     data =  [json.loads(galaxy[question + '_' + a + '_concentration']) for a in answers]
#     all_samples = np.array(data).transpose(1, 0, 2)

#     ax = ax0
#     for model_n, samples in enumerate(all_samples):
#         all_probs = []
#         color = colors[model_n]
#         n_samples = samples.shape[1]  # answer, dropout
#         for d in range(n_samples):
#             concentrations = tf.constant(samples[:, d].astype(np.float32))  # answer, dropout
#             probs = tfp.distributions.DirichletMultinomial(total_votes, concentrations).prob(x)
#             all_probs.append(probs)
#             ax.plot(votes_this_answer, probs, alpha=.15, color=color)
#         mean_probs = np.array(all_probs).mean(axis=0)
#         ax.plot(votes_this_answer, mean_probs, linewidth=2., color=color)

#     volunteer_response = galaxy[question + '_' + answer]
#     ax.axvline(volunteer_response, color='k', linestyle='--')
        
#     ax.set_xlabel(question.capitalize().replace('-', ' ') + ' "' + answer.capitalize().replace('-', ' ') + '" count')
#     ax.set_ylabel(r'$p$(count)')

#     ax = ax1
#     # ax.imshow(np.array(Image.open(galaxy['file_loc'].replace('/media/walml/beta/decals/png_native', 'png'))))
#     ax.imshow(np.array(Image.open(galaxy['file_loc'].replace('/media/walml/beta/decals/png_native', '/media/walml/beta1/galaxy_zoo/gz2'))))
#     ax.axis('off')
        
#     fig.tight_layout()
#     st.write(fig)


st.set_page_config(
    layout="wide",
    page_title='GZ DECaLS',
    page_icon='gz_icon.jpeg'
)

@st.cache
def load_data():
    df_locs = ['decals_{}.csv'.format(n) for n in range(4)]
    dfs = [pd.read_csv(df_loc) for df_loc in df_locs]
    return pd.concat(dfs)



if __name__ == '__main__':

    logging.basicConfig(level=logging.CRITICAL)

    df = load_data()

    main(df)


# https://discuss.streamlit.io/t/values-slider/9434 streamlit sharing has a temp bug that sliders only show the top value
==========
ebcf_alexa
==========


About
=====

An Alexa skill for `Elliot Bay Crossfit`_. This skill queries the `EBCF WOD API`_ (written by `Samantha Brender`_) for a fast lookup of the WOD of the day.
It gently massages the text written by `Rohan`_, the owner, into Alexa-compliant `SSML`_.


Development
===========

This project requires Python 3.6.

To run unit tests::

    $ python3 setup.py test

Deployment
==========

I will be rigging up `CodePipelines`_ to auto-deploy changes from this repo's master branch to `AWS Lambda`_, where the
code is executed from by the Alexa service. The pipeline should run the unit tests which should guard against breakage.


License
=======

The software in this repository is governed by the `MIT License`_. See `LICENSE`_.

Elliot Bay Crossfit is a trademark of Elliot Bay Crossfit and Rohan P Joseph.


.. _`Elliot Bay Crossfit`: http://www.elliottbaycrossfit.com/
.. _`EBCF WOD API`: https://github.com/samb0303/ebcf
.. _`Samantha Brender`: https://github.com/samb0303
.. _`Rohan`: https://www.facebook.com/rohan.joseph.961
.. _`SSML`: https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/speech-synthesis-markup-language-ssml-reference
.. _`CodePipelines`: https://aws.amazon.com/codepipeline/
.. _`AWS Lambda`: https://aws.amazon.com/lambda/
.. _`MIT License`: https://choosealicense.com/licenses/mit/
.. _`LICENSE`: https://github.com/dmotles/ebcf-alexa/blob/master/LICENSE

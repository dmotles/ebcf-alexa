from setuptools import setup
from distutils.cmd import Command
from datetime import datetime
import os

class Deploy(Command):
    DEFAULT_S3_BUCKET = 'motles.ebcf.alexa.skill'
    DEFAULT_LAMBDA_FUNC = 'ebcf-getwod'

    description = 'Deploy to AWS lambda'
    user_options = [
        ('s3-bucket=', 'b', 'S3 bucket to upload to'),
        ('lambda-func-name=', 'l', 'Lambda function to update'),
    ]

    def initialize_options(self):
        self.s3_bucket = None
        self.lambda_func_name = None

    def finalize_options(self):
        self.s3_bucket = self.s3_bucket or self.DEFAULT_S3_BUCKET
        self.lambda_func_name = self.lambda_func_name or self.DEFAULT_LAMBDA_FUNC

    def run(self):
        #self.spawn(['rm', '-rvf', 'build'])
        self.run_command('build')
        self.spawn(['pip', 'install', 'pytz', '-t', 'build/lib'])
        archive_base = 'ebcf_alexa_slug-' + datetime.now().strftime('%Y%m%dT%H%M%S')
        archive_path = self.make_archive(archive_base, format='zip', root_dir='build/lib')
        archive_name = os.path.basename(archive_path)
        self.spawn(['aws', 's3', 'cp', archive_path, 's3://' + self.s3_bucket + '/' + archive_name])
        self.spawn(['aws', 'lambda', 'update-function-code',
                    '--function-name', self.lambda_func_name,
                    '--s3-bucket', self.s3_bucket,
                    '--s3-key', archive_name])
        self.spawn(['rm', archive_path])

setup(
    name='ebcf_alexa',
    version='1.0',
    description='An Alexa Custom Skill for getting the WOD for Elliot Bay Crossfit',
    url='http://github.com/dmotles/ebcf_alexa',
    author='Daniel Motles',
    author_email='seltom.dan@gmail.com',
    license='MIT',
    packages=['_ebcf_alexa'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=['pytz'],
    cmdclass={'deploy': Deploy},
    py_modules=['ebcf_alexa']
)

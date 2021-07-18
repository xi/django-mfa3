from setuptools import find_packages, setup


setup(
    name='django-mfa3',
    description='multi factor authentication for django',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/xi/django-mfa3',
    author='Tobias Bengfort',
    author_email='tobias.bengfort@posteo.de',
    version='0.2.5',
    license='MIT',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=['pyotp', 'fido2', 'qrcode', 'django>=2.2'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)

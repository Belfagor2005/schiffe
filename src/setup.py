from setuptools import setup
import setup_translate

pkg = 'Extensions.Schiffe'
setup(name='enigma2-plugin-extensions-schiffe',
       version='7.1.1',
       description='Schiffe Battleship Game FHD Modded by Lululla',
       package_dir={pkg: 'Schiffe'},
       packages=[pkg],
       package_data={pkg: ['images/*.png', '*.png', '*.xml', 'locale/*/LC_MESSAGES/*.mo', 'Schiffe.png', 'pic/*.png', 'pic/*.jpg']},
       cmdclass=setup_translate.cmdclass,  # for translation
      )

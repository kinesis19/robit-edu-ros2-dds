from setuptools import setup

package_name = 'robit_blackbox'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ROBIT',
    maintainer_email='maintainer@example.com',
    description='ROBIT ROS 2 middleware (DDS) blackbox robot assignment',
    license='MIT',
    entry_points={
        'console_scripts': [
            'robot = robit_blackbox.robot:main',
            'status = robit_blackbox.status:main_status',
            'report = robit_blackbox.status:main_report',
            'check3 = robit_blackbox.check3:main',
        ],
    },
)

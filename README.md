100seconds
==========

Quick start
-----------

<pre>
cd wffplanner
virtualenv --distribute --no-site-packages env
source env/bin/activate
pip install -r requirements.txt
cp wffplanner/localsettings.py{.template,}
./manage.py syncdb --migrate
./manage.py runserver
</pre>

Open [http://localhost:8000/](localhost:8000) in your browser. Should work!
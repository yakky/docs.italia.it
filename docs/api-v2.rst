Read the Docs Public API V2
===========================

Primary Objects
---------------

Read the Docs has a number of objects that we expose via our API.
The main objects are:

* Projects
* Versions
* Builds
* Users

They make up the core of the project.

Secondary Objects
-----------------

We also have a number of objects that are secondary in nature.
They are mostly project-specific,
or tied to users.
These will be included also in the API:

* Domains
* Files
* Notifications

Authentication
--------------

Users will be authenticated with either:

* Username & Password
* API Token 

Each of these methods will tie a request to a user.

Authorization
-------------

Each request will be authorized based on the user making the request.
Each object will have specific authorization,
which is defined here.

There will be three general levels of authorization:

* Unauthenticated
* Authenticated
* Owner/Admin

Users
~~~~~

Unauthenticated users will have no access to this API.

Authenticated users will be able to:

* Update user information

Projects
~~~~~~~~

Unauthenticated users will be able to:

* List public projects
* Filter public projects by [name, slug, other attributes]

Authenticated users will be able to:

* List private projects they have access to
* Create a new Project
* [Admin] Update Projects 
* [Admin] Delete Projects 

Versions
~~~~~~~~

Unauthenticated users will be able to:

* List public Versions
* Filter public Versions by [name, slug, other attributes]

Authenticated users will be able to:

* List private versions they have access to
* [Admin] Make a version Active
* [Admin] Change a version's privacy level

.. note:: Version's can't be added or deleted because they are maintained 
		  by the build system and mapped to Version Control.


Builds
~~~~~~

Unauthenticated users will be able to:

* List public Builds
* Filter public Builds by [name, slug, other attributes]

Authenticated users will be able to:

* List private Builds they have access to
* [Admin] Trigger a new build for a project

.. note:: Build's are created by Read the Docs,
		  and as such can't be deleted or edited via the API



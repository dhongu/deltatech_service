Organizations that own, rent or hold land and buildings on loan or concession need one register of them. This module adds a *Property* app for lands, buildings and rooms.

- **Lands**: A land has a location type (*Intravilan* or *Extravilan*), cadastral references, a price per m² and a *Total Price* computed from its surface.
- **Buildings**: A building links to a land and has a category, a two-level purpose, valuation figures, countable features such as extinguishers, and a tenant history.
- **Rooms**: A room records level, dimensions, floor type and tenant when rented, and computes its disinsection area. Saving is refused if its floor cleaning area exceeds its surface.
- **Building totals**: Areas per *Room usage* and for cleaning and disinsection are summed from the building's rooms, but its form does not show them.
- **Coded lists**: The lists *Acquisition Mode*, *Building Purpose* and *Region* hold codes and names under *Configurations*. Typing digits in such a field searches the code.

It depends on *Maintenance* (`maintenance`) and *Discuss* (`mail`), and each land and building is also a maintenance equipment record. The *Location* button opens Google Maps in a new tab with the coordinates. Internal users have access; rooms, features and tenant history follow the user's companies and followed buildings. It also adds *Land* and *Building* as contact types.

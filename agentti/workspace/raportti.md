Tietokannassa on kuusi taulua:

1. **Categories**  
   - `category_id` (BIGINT)  
   - `name` (VARCHAR)  
   - `x_min`, `x_max`, `y_min`, `y_max` (DOUBLE) – määrittelevät alueen koordinaatit

2. **Quality**  
   - `quality_id` (BIGINT)  
   - `node_id` (VARCHAR)  
   - `zone_id` (BIGINT)  
   - `is_valid` (BOOLEAN)  
   - `reason` (VARCHAR)  
   - `more_info` (VARCHAR) – mahdolliset tarkennukset laadun arvioinnista

3. **ShoppingCart**  
   - `node_id` (VARCHAR)  
   - `description` (VARCHAR) – esineiden tai tuotteiden kuvaukset

4. **Visit**  
   - `visit_id` (VARCHAR)  
   - `node_id` (VARCHAR)  
   - `duration_seconds` (BIGINT)  
   - `start_time`, `end_time` (TIMESTAMP) – vierailun aikarajat

5. **Zone**  
   - `zone_id` (BIGINT)  
   - `visit_id` (VARCHAR)  
   - `x`, `y` (DOUBLE) – sijaintikoordinaatit  
   - `timestamp` (TIMESTAMP) – paikannuksen aikaleima  
   - *Huom: ~10M riviä*

6. **ZoneVisit**  
   - `zone_visit_id` (BIGINT)  
   - `visit_id` (VARCHAR)  
   - `category_id` (BIGINT)  
   - `start_time`, `end_time` (TIMESTAMP) – vierailun aikarajat tietyn kategorian alueella

Taulujen väliset suhteet:  
- `Visit.visit_id` liittyy `Zone.visit_id` ja `ZoneVisit.visit_id`  
- `Zone.zone_id` liittyy `Quality.zone_id`  
- `ZoneVisit.category_id` liittyy `Categories.category_id`  
- `ShoppingCart.node_id` liittyy `Visit.node_id`

Tietokanta näyttää hallitsevan UWB-paikannusdataa, jossa vierailut (Visit), alueet (Zone), kategoriat (Categories), laatu (Quality), ostoskorit (ShoppingCart) ja aluevierailut (ZoneVisit) ovat keskeisiä käsitteitä.
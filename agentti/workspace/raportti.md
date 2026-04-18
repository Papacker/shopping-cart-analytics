Tietokannassa on kuusi taulua:

1. **Categories**  
   - `category_id` (BIGINT)  
   - `name` (VARCHAR)  
   - `x_min`, `x_max`, `y_min`, `y_max` (DOUBLE) – mahdollisesti alueen raja-arvot

2. **Quality**  
   - `quality_id` (BIGINT)  
   - `node_id` (VARCHAR)  
   - `zone_id` (BIGINT)  
   - `is_valid` (BOOLEAN)  
   - `reason` (VARCHAR)  
   - `more_info` (VARCHAR) – laadun arviointitiedot

3. **ShoppingCart**  
   - `node_id` (VARCHAR)  
   - `description` (VARCHAR) – ostoskorin sisältö

4. **Visit**  
   - `visit_id` (VARCHAR)  
   - `node_id` (VARCHAR)  
   - `duration_seconds` (BIGINT)  
   - `start_time`, `end_time` (TIMESTAMP) – vierailutiedot

5. **Zone**  
   - `zone_id` (BIGINT)  
   - `visit_id` (VARCHAR)  
   - `x`, `y` (DOUBLE) – sijaintikoordinaatit  
   - `timestamp` (TIMESTAMP) – aikaleima

6. **ZoneVisit**  
   - `zone_visit_id` (BIGINT)  
   - `visit_id` (VARCHAR)  
   - `category_id` (BIGINT)  
   - `start_time`, `end_time` (TIMESTAMP) – vieraillun alueen aikajana

Taulujen väliset suhteet viittaavat sijaintipohjaisiin vierailu- ja laaduntarkkailudataan, mahdollisesti UWB-teknologiaa hyödyntävään järjestelmään.
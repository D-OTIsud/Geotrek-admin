-------------------------------------------------------------------------------
-- Force Path default values
-- Django does not translate model default value to
-- database default column values.
-------------------------------------------------------------------------------

ALTER TABLE core_path ALTER COLUMN date_insert SET DEFAULT now();
ALTER TABLE core_path ALTER COLUMN date_update SET DEFAULT now();
ALTER TABLE core_path ALTER COLUMN departure SET DEFAULT '';
ALTER TABLE core_path ALTER COLUMN arrival SET DEFAULT '';
ALTER TABLE core_path ALTER COLUMN valid SET DEFAULT false;
ALTER TABLE core_path ALTER COLUMN visible SET DEFAULT true;



-------------------------------------------------------------------------------
-- Add spatial index (will boost spatial filters)
-------------------------------------------------------------------------------

DROP INDEX IF EXISTS troncons_geom_idx;
DROP INDEX IF EXISTS l_t_troncon_geom_idx;
DROP INDEX IF EXISTS core_path_geom_idx;
CREATE INDEX core_path_geom_idx ON core_path USING gist(geom);

DROP INDEX IF EXISTS troncons_start_point_idx;
DROP INDEX IF EXISTS l_t_troncon_start_point_idx;
DROP INDEX IF EXISTS core_path_start_point_idx;
CREATE INDEX core_path_start_point_idx ON core_path USING gist(ST_StartPoint(geom));

DROP INDEX IF EXISTS troncons_end_point_idx;
DROP INDEX IF EXISTS l_t_troncon_end_point_idx;
DROP INDEX IF EXISTS core_path_end_point_idx;
CREATE INDEX core_path_end_point_idx ON core_path USING gist(ST_EndPoint(geom));

DROP INDEX IF EXISTS troncons_geom_cadastre_idx;
DROP INDEX IF EXISTS l_t_troncon_geom_cadastre_idx;
DROP INDEX IF EXISTS core_path_geom_cadastre_idx;
CREATE INDEX core_path_geom_cadastre_idx ON core_path USING gist(geom_cadastre);

DROP INDEX IF EXISTS l_t_troncon_geom_3d_idx;
DROP INDEX IF EXISTS core_path_geom_3d_idx;
CREATE INDEX core_path_geom_3d_idx ON core_path USING gist(geom_3d);

-------------------------------------------------------------------------------
-- Keep dates up-to-date
-------------------------------------------------------------------------------

DROP TRIGGER IF EXISTS l_t_troncon_date_insert_tgr ON core_path;
DROP TRIGGER IF EXISTS core_path_date_insert_tgr ON core_path;
CREATE TRIGGER core_path_date_insert_tgr
    BEFORE INSERT ON core_path
    FOR EACH ROW EXECUTE PROCEDURE ft_date_insert();

DROP TRIGGER IF EXISTS l_t_troncon_date_update_tgr ON core_path;
DROP TRIGGER IF EXISTS core_path_date_update_tgr ON core_path;
CREATE TRIGGER core_path_date_update_tgr
    BEFORE INSERT OR UPDATE ON core_path
    FOR EACH ROW EXECUTE PROCEDURE ft_date_update();


-------------------------------------------------------------------------------
-- Check overlapping paths
-------------------------------------------------------------------------------

DROP FUNCTION IF EXISTS check_path_not_overlap(integer, geometry) CASCADE;

CREATE FUNCTION {# geotrek.core #}.check_path_not_overlap(pid integer, line geometry) RETURNS BOOL AS $$
DECLARE
    t_count integer;
    tolerance float;
BEGIN
    -- Note: I gave up with the idea of checking almost overlap/touch.

    -- tolerance := 1.0;
    -- Crossing and extremity touching is OK.
    -- Overlapping and --almost overlapping-- is KO.
    SELECT COUNT(*) INTO t_count
    FROM core_path
    WHERE pid != id
      AND ST_GeometryType(ST_intersection(geom, line)) IN ('ST_LineString', 'ST_MultiLineString');
      -- not extremity touching
      -- AND ST_Touches(geom, line) = false
      -- not crossing
      -- AND ST_GeometryType(ST_intersection(geom, line)) NOT IN ('ST_Point', 'ST_MultiPoint')
      -- overlap is a line
      -- AND ST_GeometryType(ST_intersection(geom, ST_buffer(line, tolerance))) IN ('ST_LineString', 'ST_MultiLineString')
      -- not almost touching, at most twice
      -- AND       ST_Length(ST_intersection(geom, ST_buffer(line, tolerance))) > (4 * tolerance);
    RETURN t_count = 0;
END;
$$ LANGUAGE plpgsql;


-------------------------------------------------------------------------------
-- Update geometry of related topologies
-------------------------------------------------------------------------------

DROP TRIGGER IF EXISTS l_t_troncon_evenements_geom_u_tgr ON core_path;
DROP TRIGGER IF EXISTS l_t_troncon_90_evenements_geom_u_tgr ON core_path;
DROP TRIGGER IF EXISTS core_path_90_topologies_geom_u_tgr ON core_path;
DROP FUNCTION IF EXISTS update_evenement_geom_when_troncon_changes() CASCADE;
DROP FUNCTION IF EXISTS update_topology_geom_when_path_changes() CASCADE;

CREATE FUNCTION {# geotrek.core #}.update_topology_geom_when_path_changes() RETURNS trigger SECURITY DEFINER AS $$
DECLARE
    eid integer;
    egeom geometry;
    linear_offset float;
    side_offset float;
BEGIN
    -- Geometry of linear topologies are always updated
    -- Geometry of point topologies are updated if offset = 0
    FOR eid IN SELECT e.id
               FROM core_pathaggregation et, core_topology e
               WHERE et.path_id = NEW.id AND et.topo_object_id = e.id
               GROUP BY e.id, e."offset"
               HAVING BOOL_OR(et.start_position != et.end_position) OR e."offset" = 0.0
    LOOP
        PERFORM update_geometry_of_topology(eid);
    END LOOP;

    -- Special case of point geometries with offset != 0
    FOR eid, egeom IN SELECT e.id, e.geom
               FROM core_pathaggregation et, core_topology e
               WHERE et.path_id = NEW.id AND et.topo_object_id = e.id
               GROUP BY e.id, e.geom, e."offset"
               HAVING COUNT(et.id) = 1 AND BOOL_OR(et.start_position = et.end_position) AND e."offset" != 0.0
    LOOP
        SELECT * INTO linear_offset, side_offset FROM ST_InterpolateAlong(NEW.geom, egeom) AS (position float, distance float);
        UPDATE core_topology SET "offset" = side_offset WHERE id = eid;
        UPDATE core_pathaggregation SET start_position = linear_offset, end_position = linear_offset WHERE topo_object_id = eid AND path_id = NEW.id;
    END LOOP;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER core_path_90_topologies_geom_u_tgr
AFTER UPDATE OF geom ON core_path
FOR EACH ROW EXECUTE PROCEDURE update_topology_geom_when_path_changes();


-------------------------------------------------------------------------------
-- Ensure paths have valid geometries
-------------------------------------------------------------------------------

ALTER TABLE core_path DROP CONSTRAINT IF EXISTS l_t_troncon_geom_isvalid;
ALTER TABLE core_path DROP CONSTRAINT IF EXISTS core_path_geom_isvalid;
ALTER TABLE core_path ADD CONSTRAINT core_path_geom_isvalid CHECK (ST_IsValid(geom));

ALTER TABLE core_path DROP CONSTRAINT IF EXISTS troncons_geom_issimple;
ALTER TABLE core_path DROP CONSTRAINT IF EXISTS l_t_troncon_geom_issimple;
ALTER TABLE core_path DROP CONSTRAINT IF EXISTS core_path_geom_issimple;
ALTER TABLE core_path ADD CONSTRAINT core_path_geom_issimple CHECK (ST_IsSimple(geom));


-------------------------------------------------------------------------------
-- Compute elevation and elevation-based indicators
-------------------------------------------------------------------------------

DROP TRIGGER IF EXISTS l_t_troncon_elevation_iu_tgr ON core_path;
DROP TRIGGER IF EXISTS l_t_troncon_10_elevation_iu_tgr ON core_path;
DROP TRIGGER IF EXISTS core_path_10_elevation_iu_tgr ON core_path;
DROP FUNCTION IF EXISTS elevation_troncon_iu() CASCADE;
DROP FUNCTION IF EXISTS elevation_path_iu() CASCADE;

CREATE FUNCTION {# geotrek.core #}.elevation_path_iu() RETURNS trigger SECURITY DEFINER AS $$
DECLARE
    elevation elevation_infos;
BEGIN

    SELECT * FROM ft_elevation_infos(NEW.geom, {{ ALTIMETRIC_PROFILE_STEP }}) INTO elevation;
    -- Update path geometry
    NEW.geom_3d := elevation.draped;
    NEW.length := ST_3DLength(elevation.draped);
    NEW.slope := elevation.slope;
    NEW.min_elevation := elevation.min_elevation;
    NEW.max_elevation := elevation.max_elevation;
    NEW.ascent := elevation.positive_gain;
    NEW.descent := elevation.negative_gain;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER core_path_10_elevation_iu_tgr
BEFORE INSERT OR UPDATE OF geom ON core_path
FOR EACH ROW EXECUTE PROCEDURE elevation_path_iu();


-------------------------------------------------------------------------------
-- Change status of related objects when paths are deleted
-------------------------------------------------------------------------------

DROP TRIGGER IF EXISTS l_t_troncon_related_objects_d_tgr ON core_path;
DROP TRIGGER IF EXISTS core_path_related_objects_d_tgr ON core_path;
DROP FUNCTION IF EXISTS troncons_related_objects_d() CASCADE;
DROP FUNCTION IF EXISTS paths_related_objects_d() CASCADE;

CREATE FUNCTION {# geotrek.core #}.paths_related_objects_d() RETURNS trigger SECURITY DEFINER AS $$
DECLARE
BEGIN
    -- Mark empty topologies as deleted
    UPDATE core_topology e
        SET deleted = TRUE
        FROM core_pathaggregation et
        WHERE et.topo_object_id = e.id AND et.path_id = OLD.id AND NOT EXISTS(
            SELECT * FROM core_pathaggregation
            WHERE topo_object_id = e.id AND path_id != OLD.id
        );

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER core_path_related_objects_d_tgr
BEFORE DELETE ON core_path
FOR EACH ROW EXECUTE PROCEDURE paths_related_objects_d();


---------------------------------------------------------------------
-- Make sure cache key (base on lastest updated) is refresh on DELETE
---------------------------------------------------------------------

DROP TRIGGER IF EXISTS l_t_troncon_latest_updated_d_tgr ON core_path;
DROP TRIGGER IF EXISTS core_path_latest_updated_d_tgr ON core_path;
DROP FUNCTION IF EXISTS troncon_latest_updated_d() CASCADE;
DROP FUNCTION IF EXISTS path_latest_updated_d() CASCADE;

CREATE FUNCTION {# geotrek.core #}.path_latest_updated_d() RETURNS trigger SECURITY DEFINER AS $$
DECLARE
BEGIN
    -- Touch latest path
    UPDATE core_path SET date_update = NOW()
    WHERE id IN (SELECT id FROM core_path ORDER BY date_update DESC LIMIT 1);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER core_path_latest_updated_d_tgr
AFTER DELETE ON core_path
FOR EACH ROW EXECUTE PROCEDURE path_latest_updated_d();

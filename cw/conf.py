import jinja2, os, sys, yaml

from cw import appcon

class CromwellConf(object):
    def __init__(self, attrs):
        self._attrs = attrs
        self.is_validated = False

    ## ATTRIBUTES
    def get(self, name, group="general"):
        if name in self._attrs:
            return self._attrs[name]
        return None

    def set(self, name, value, group="general"):
        self._attrs[name] = value
        return value

    def getattr(self, name):
        if name not in self.attribute_names():
            raise Exception(f"Unknown attribute <{name}>")
        if name in self._attrs:
            return self._attrs[name]
        return None

    def setattr(self, name, value):
        if name not in self.attribute_names():
            raise Exception(f"Unknown attribute <{name}>")
        self._attrs[name] = value
        return value

    @staticmethod
    def known_attributes():
        return {
                # ATTR: [value, required]
                "CROMWELL_DIR": [os.getcwd, True],
                "CROMWELL_PORT": ["8888", True],
                "LSF_DOCKER_VOLUMES": ["/scratch1/fs1/hprc:/scratch1/fs1/hprc /storage1/fs1/hprc:/storage1/fs1/hprc", True],
                "LSF_JOB_GROUP": [None, True],
                "LSF_QUEUE": [None, True],
                "LSF_USER_GROUP": [None, True],
                "CROMWELL_JOB_ID": [None, False],
                "CROMWELL_HOST": [None, False],
                "CROMWELL_URL": [None, False],
                }

    @staticmethod
    def attribute_names():
        return CromwellConf.known_attributes().keys()

    def required_attribute_names():
        names = set()
        known_attrs = CromwellConf.known_attributes()
        for name, (value, isrequired) in known_attrs.items():
            if isrequired:
                names.add(name)
        return names

    def default_attributes():
        attrs = {}
        known_attrs = CromwellConf.known_attributes()
        #for name, (value, isrequired) in known_attrs.items():
        for name, (value, isrequired) in known_attrs.items():
            if callable(value):
                value = value()
            attrs[name] = value
        return attrs

    def validate_attributes(self):
        e = []
        for name in CromwellConf.required_attribute_names():
            value = self.get(name)
            if value is None:#if a not in attrs or attrs[a] is None or attrs[a] == "null":
                e.append(name)
        if len(e):
            raise Exception(f"Missing or undefined attributes: {' | '.join(e)}")
        self.is_validated = True
    ##-

    ## SAVE / LOAD
    @staticmethod
    def yaml_fn():
        return "cw.yaml"

    def save(self):
        yaml_fn = CromwellConf.yaml_fn()
        with open(yaml_fn, "w") as f:
            f.write(yaml.dump(self._attrs))

    def safe_load():
        yaml_fn = CromwellConf.yaml_fn()
        if os.path.exists(yaml_fn):
            return CromwellConf.load(yaml_fn)
        return CromwellConf(CromwellConf.default_attributes())

    def load(yaml_fn="cw.yaml"):
        yaml_file = CromwellConf.yaml_fn()
        if not os.path.exists(yaml_file):
            raise Exception(f"Cannot create config object, given YAML file <{yaml_file}> does not exist!")
        with open(yaml_fn, "r") as f:
            attrs = yaml.safe_load(f)
        self = CromwellConf(attrs)
        self.validate_attributes()
        self._attrs["CROMWELL_DIR"] = os.path.abspath(self._attrs["CROMWELL_DIR"])
        return self
    ##--

    def write_server_files(self):
        server_dn = appcon.get("server_dn")
        for name in ("conf", "run", "start"):
            fn = appcon.get(group="server", name=f"{name}_fn")
            fun = getattr(self, f"server_{name}_content")
            with open(fn, "w") as f:
                f.write(fun())

    def server_conf_content(self):
        with open(appcon.get(group="resources", name="conf_template_fn"), "r") as f:
            template = jinja2.Template(f.read())
        attrs = {
                "RUNS_DIR": appcon.get("runs_dn"),
                "DB_DIR": appcon.get("db_dn"),
                "LOGS_DIR": appcon.get("logs_dn"),
                "SERVER_PORT": appcon.get(group="server", name="port"),
                "LSF_DOCKER_VOLUMES": appcon.get(group="lsf", name="docker_volumes"),
                "LSF_JOB_GROUP": appcon.get(group="lsf", name="job_group"),
                "LSF_QUEUE": appcon.get(group="lsf", name="user_group"),
                "LSF_USER_GROUP": appcon.get(group="lsf", name="user_group"),
                }
        return template.render(attrs)

    def server_run_content(self):
        template_fn = appcon.get(group="resources", name="run_template_fn")
        attrs = { # put in validating method
                "SERVER_PORT": appcon.get(group="server", name="port"),
                "SERVER_DN": appcon.dn_for("server"),
                #"SERVER_LOG_FN": appcon.get(group="server", name="log_fn"),
                #"SERVER_RUN_FN": appcon.get(group="server", name=run_fn"),
                "LSF_DOCKER_VOLUMES": appcon.get(group="lsf", name="docker_volumes"),
                "LSF_JOB_GROUP": appcon.get(group="lsf", name="job_group"),
                "LSF_QUEUE": appcon.get(group="lsf", name="user_group"),
                "LSF_USER_GROUP": appcon.get(group="lsf", name="user_group"),
                }
        return self._generate_content(template_fn=template_fn, attrs=attrs)

    def server_start_content(self):
        attrs = {"SERVER_CONF_FN": appcon.get(group="server", name="conf_fn")}
        template_fn = appcon.get(group="resources", name="start_template_fn")
        return self._generate_content(template_fn=template_fn, attrs=attrs)

    ###
    def _generate_content(self, template_fn, attrs):
        if not os.path.exists(template_fn):
            raise Exception(f"Template file {template_fn} does not exist!")
        with open(template_fn, "r") as f:
            template = jinja2.Template(f.read())
        return template.render(**attrs)
    ##-
#-- CromwellConf

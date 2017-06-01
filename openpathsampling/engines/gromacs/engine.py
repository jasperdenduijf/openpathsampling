"""
Gromacs support in OpenPathSampling

OpenPathSampling supports Gromacs as an "external engine," meaning that
Gromacs itself runs as a coprocess, and OPS uses the file system as an
intermediary to monitor when a path needs to be terminated.
"""

import logging

from mdtraj.formats import TRRTrajectoryFile

from openpathsampling.engines import ExternalEngine
from openpathsampling.engines import features
from openpathsampling.engines.snapshot import BaseSnapshot
import features as gmx_features

import os
import psutil
import shlex
import numpy as np

# TODO: all gmx_features should be moved to external_md

@features.base.attach_features([
    features.engine,
    gmx_features.coordinates,
    gmx_features.velocities,
    gmx_features.box_vectors,
    gmx_features.file_info
])
class ExternalMDSnapshot(BaseSnapshot):
    """
    Snapshot for external MD engines

    Internally, this only stores the file_number and the file_position. All
    specific details (positions, velocities, box vectors) are loaded from
    file when requested.
    """
    def __init__(self, file_number=None, file_position=None, engine=None):
        self.file_number = file_number
        self.file_position = file_position
        self.engine = engine
        self._xyz = None
        self._velocities = None
        self._box_vectors = None

    def load_details(self):
        filename = self.engine.trajectory_filename(self.file_number)
        (xyz, vel, box) = self.engine.read_frame_data(filename,
                                                      self.file_position)
        self._xyz = xyz
        self._velocities = vel
        self._box_vectors = box

    def clear_cache(self):
        self._xyz = None
        self._velocities = None
        self._box_vectors = None

    def __repr__(self):
        num_str = "file_number=" + str(self.file_number)
        pos_str = "file_position=" + str(self.file_position)
        eng_str = "engine=" + repr(self.engine)
        args = ", ".join([num_str, pos_str, eng_str])
        return "{cls_str}(".format(cls_str=self.cls) + args + ")"


class Gromacs5Engine(ExternalEngine):
    def __init__(self, gro, mdp, top, options, name="gmx"):
        self.gro = gro
        self.mdp = mdp
        self._file = None  # file open/close efficiency
        self._last_filename = None
        # TODO: update options with correct n_spatial, n_atoms
        # TODO: add snapshot_timestep; first via options, later read mdp
        template = None  # TODO: extract a template from the gro
        super(Gromacs5Engine, self).__init__(options, template)
        self.named(name)

    def read_frame_data(self, filename, frame_num):
        """
        Returns pos, vel, box or raises error
        """
        if self._last_filename != filename:
            try:
                self._file.close()
            except AttributeError:
                pass  # first time thru, self._file is None
            self._file = TRRTrajectoryFile(filename)
        self._file.seek(offset=frame_num)
        data = self._file._read(n_frames=1, atom_indices=None,
                                get_velocities=True)
        return data[0][0], data[5][0], data[3][0]

    def read_frame_from_file(self, filename, frame_num):
        # note: this only needs to return the file pointers -- but should
        # only do so once that frame has been written!
        basename = os.path.basename(filename)
        # basename should be in the format [0-9]+\.trr (as set by the
        # trajectory_filename method)
        file_number = int(basename.split('.')[0])
        try:
            self.read_frame_data(filename, frame_num)
        except IndexError:
            # this means that no such frame exists yet, so we return None
            return None
        except RuntimeError as e:
            # TODO: matches "TRR read error"
            return 'partial'
        else:
            return ExternalMDSnapshot(file_number=file_number,
                                      file_position=frame_num,
                                      engine=self)

    def write_frame_to_file(self, filename, snapshot, mode='w'):
        if os.path.isfile(filename):
            # stop if we already have this file; could also happen because
            # of a weird behavior in a mover. You must remove the files if
            # you don't want them.
            raise RuntimeError("File " + str(filename) + " exists. "
                               + "Preventing overwrite.")
        trr = TRRTrajectoryFile(filename, mode)
        # type control before passing things to Cython code
        xyz = np.asarray([snapshot.xyz], dtype=np.float32)
        time = np.asarray([0.0], dtype=np.float32)
        step = np.asarray([0], dtype=np.int32)
        box = np.asarray([snapshot.box_vectors], dtype=np.float32)
        lambd = np.asarray([0.0], dtype=np.float32)
        vel = np.asarray([snapshot.velocities], dtype=np.float32)
        trr._write(xyz, time, step, box, lambd, vel)
        trr.close()

    def trajectory_filename(self, number):
        trr_dir = self.name + "_trr/"
        return trr_dir + '{:07d}'.format(number) + '.trr'

    def set_filenames(self, number):
        self.input_file = "initial_frame.trr"
        self.output_file = self.trajectory_filename(number + 1)
        num_str = '{:07d}'.format(number)
        self.edr_file = os.path.join([self.name + "_edr", num_str + '.edr'])
        self.log_file = os.path.join([self.name + "_log", num_str + '.log'])

    def prepare(self):
        # gmx grompp -c conf.gro -f md.mdp -t initial_frame.trr -p topol.top
        cmd = "gmx grompp -c {gro} -f {mdp} -p {top} -t {inp}".format(
            gro=self.gro, mdp=self.mdp, top=self.top, inp=self.input_file
        )
        run_cmd = shlex.split(cmd)
        return_code = psutil.Popen(run_cmd, preexec_fn=os.setsid).wait()
        print return_code  # TODO: what are the appropriate values here?

    def engine_command(self):
        # gmx mdrun -s topol.tpr -o trr/0000001.trr -g 0000001.log
        cmd = "gmx mdrun -s topol.tpr -o {out} -e {edr} -g {log} {args}"
        cmd = cmd.format(out=self.output_file,
                         edr=self.edr_file,
                         log=self.log_file,
                         args=self.options['mdrun_args'])
        return cmd

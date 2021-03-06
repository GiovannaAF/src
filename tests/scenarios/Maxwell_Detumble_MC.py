''' '''
'''
 ISC License

 Copyright (c) 2016, Autonomous Vehicle Systems Lab, University of Colorado at Boulder

 Permission to use, copy, modify, and/or distribute this software for any
 purpose with or without fee is hereby granted, provided that the above
 copyright notice and this permission notice appear in all copies.

 THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

'''

#
# Basilisk Integrated Test
#
# Purpose:  Integrated test of the MonteCarlo module.  Runs multiple
#           scenarioAttitudeFeedbackRW with dispersed initial parameters
#


import inspect
import math
import os
import numpy as np
import shutil
import matplotlib.pyplot as plt

DATASHADER_FOUND = True
try:
    from Basilisk.utilities import datashaderGraphingInterface as datashaderLibrary
except ImportError:
    print "Datashader library not found. Will use matplotlib"
    DATASHADER_FOUND = False


# @cond DOXYGEN_IGNORE
filename = inspect.getframeinfo(inspect.currentframe()).filename
fileNameString = os.path.basename(os.path.splitext(__file__)[0])
path = os.path.dirname(os.path.abspath(filename))
# @endcond

from Basilisk import __path__
bskPath = __path__[0]
from datetime import datetime

# import general simulation support files
from Basilisk.utilities import SimulationBaseClass
from Basilisk.utilities import unitTestSupport                  # general support file with common unit test functions
from Basilisk.utilities import macros
from Basilisk.utilities import orbitalMotion
from Basilisk.utilities import simIncludeGravBody

# import simulation related support
from Basilisk.simulation import spacecraftPlus
from Basilisk.utilities import simIncludeGravBody
from Basilisk.simulation import simple_nav
from Basilisk.simulation import mag_meter
from Basilisk.simulation import imu_sensor
from Basilisk.simulation import coarse_sun_sensor
from Basilisk.simulation import simMessages
from Basilisk.simulation import torqueRodDynamicEffector
from Basilisk.fswAlgorithms import B_DOT

# import FSW Algorithm related support
from Basilisk.fswAlgorithms import MRP_Feedback
from Basilisk.fswAlgorithms import inertial3D
from Basilisk.fswAlgorithms import attTrackingError
from Basilisk.fswAlgorithms import cssWlsEst
from Basilisk.fswAlgorithms import sunSafePoint
from Basilisk import pyswice

# import message declarations
from Basilisk.fswAlgorithms import fswMessages

from Basilisk.utilities.MonteCarlo.Controller import Controller, RetentionPolicy
from Basilisk.utilities.MonteCarlo.Dispersions import (UniformEulerAngleMRPDispersion, UniformDispersion,
                                                       NormalVectorCartDispersion, InertiaTensorDispersion)


NUMBER_OF_RUNS = 15
VERBOSE = True



# Here are the name of some messages that we want to retain or otherwise use
inertial3DConfigOutputDataName = "guidanceInertial3D"
attErrorConfigOutputDataName = "attErrorInertial3DMsg"
bdotControlConfigOutputDataName = "LrRequested"
sNavObjectOutputTransName = "simple_trans_nav_output"
sNavObjectOutputAttName = "simple_att_nav_output"

# If using datashader, set this to 1 to graph
# from existing csv files. Otherwise, set this to 0. This is usually set in the configure()
# method at the bottom of the file
ONLY_GRAPH_DATA = 0

# We also will need the simulationTime and samplingTimes
numDataPoints = 5000
simulationTime = macros.hour2nano(5.5)
samplingTime = simulationTime / (numDataPoints-1)


def run(saveFigures, case, show_plots, useDatashader):
    '''This function is called by the py.test environment.'''

    if DATASHADER_FOUND:
        configureDatashader()

    if ONLY_GRAPH_DATA:
        return

    # A MonteCarlo simulation can be created using the `MonteCarlo` module.
    # This module is used to execute monte carlo simulations, and access
    # retained data from previously executed MonteCarlo runs.

    # First, the `Controller` class is used in order to define the simulation
    monteCarlo = Controller()

    # Every MonteCarlo simulation must define a function that creates the `SimulationBaseClass` to execute and returns it. Within this function, the simulation is created and configured
    monteCarlo.setSimulationFunction(createScenarioAttitudeFeedbackRW)

    # Also, every MonteCarlo simulation must define a function which executes the simulation that was created.
    monteCarlo.setExecutionFunction(executeScenario)

    # A Monte Carlo simulation must define how many simulation runs to execute
    monteCarlo.setExecutionCount(NUMBER_OF_RUNS)

    # The simulations can have random seeds of each simulation dispersed randomly
    monteCarlo.setShouldDisperseSeeds(True)

    # Optionally set the number of cores to use
    # monteCarlo.setThreadCount(PROCESSES)

    # Whether to print more verbose information during the run
    monteCarlo.setVerbose(VERBOSE)

    # We set up where to retain the data to.
    dirName = "montecarlo_test" + str(os.getpid())
    monteCarlo.setArchiveDir(dirName)

    # Statistical dispersions can be applied to initial parameters using the MonteCarlo module
    dispMRPInit = 'TaskList[0].TaskModels[0].hub.sigma_BNInit'
    dispOmegaInit = 'TaskList[0].TaskModels[0].hub.omega_BN_BInit'
    dispList = [dispMRPInit, dispOmegaInit]

    # Add dispersions with their dispersion type
    monteCarlo.addDispersion(UniformEulerAngleMRPDispersion(dispMRPInit))
    monteCarlo.addDispersion(NormalVectorCartDispersion(dispOmegaInit, 9.0*macros.D2R, 1*macros.D2R))

    # A `RetentionPolicy` is used to define what data from the simulation should be retained. A `RetentionPolicy`
    # is a list of messages and variables to log from each simulation run. It also has a callback,
    # used for plotting/processing the retained data.
    retentionPolicy = RetentionPolicy()
    # define the data to retain
    retentionPolicy.addMessageLog(attErrorConfigOutputDataName, [("sigma_BR", range(3)), ("omega_BR_B", range(3))], samplingTime)
    retentionPolicy.addMessageLog(sNavObjectOutputTransName, [("r_BN_N", range(3))], samplingTime)
    retentionPolicy.addMessageLog(sNavObjectOutputAttName, [("omega_BN_B", range(3))], samplingTime)

    if show_plots:
        # plot data only if show_plots is true, otherwise just retain
        retentionPolicy.setDataCallback(plotSim)
    if saveFigures:
        # plot data only if show_plots is true, otherwise just retain
        retentionPolicy.setDataCallback(plotSimAndSave)
    if useDatashader & DATASHADER_FOUND:
        # plot, populate, write using datashader
        retentionPolicy.setDataCallback(datashaderLibrary.plotSim)
    monteCarlo.addRetentionPolicy(retentionPolicy)

    if case ==1:
        # After the monteCarlo run is configured, it is executed.
        # This method returns the list of jobs that failed.
        failures = monteCarlo.executeSimulations()

        assert len(failures) == 0, "No runs should fail"

        # Now in another script (or the current one), the data from this simulation can be easily loaded.
        # This demonstrates loading it from disk
        monteCarloLoaded = Controller.load(dirName)

        # Then retained data from any run can then be accessed in the form of a dictionary with two sub-dictionaries for messages and variables:
        retainedData = monteCarloLoaded.getRetainedData(NUMBER_OF_RUNS-1)
        assert retainedData is not None, "Retained data should be available after execution"
        assert "messages" in retainedData, "Retained data should retain messages"
        assert "attErrorInertial3DMsg.sigma_BR" in retainedData["messages"], "Retained messages should exist"

        # We also can rerun a case using the same parameters and random seeds
        # If we rerun a properly set-up run, it should output the same data.
        # Here we test that if we rerun the case the data doesn't change
        oldOutput = retainedData["messages"]["attErrorInertial3DMsg.sigma_BR"]

        # Rerunning the case shouldn't fail
        failed = monteCarloLoaded.reRunCases([NUMBER_OF_RUNS-1])
        assert len(failed) == 0, "Should rerun case successfully"

        # # Now access the newly retained data to see if it changed
        # retainedData = monteCarloLoaded.getRetainedData(NUMBER_OF_RUNS-1)
        # newOutput = retainedData["messages"]["attErrorInertial3DMsg.sigma_BR"]
        # for k1, v1 in enumerate(oldOutput):
        #     for k2, v2 in enumerate(v1):
        #         assert math.fabs(oldOutput[k1][k2] - newOutput[k1][k2]) < .001, \
        #         "Outputs shouldn't change on runs if random seeds are same"

        # We can also access the initial parameters
        # The random seeds should differ between runs, so we will test that
        params1 = monteCarloLoaded.getParameters(NUMBER_OF_RUNS-1)
        params2 = monteCarloLoaded.getParameters(NUMBER_OF_RUNS-2)
        assert "TaskList[0].TaskModels[0].RNGSeed" in params1, "random number seed should be applied"
        for dispName in dispList:
            assert dispName in params1, "dispersion should be applied"
            # assert two different runs had different parameters.
            assert params1[dispName] != params2[dispName], "dispersion should be different in each run"

        # Now we execute our callback for the retained data.
        # For this run, that means executing the plot.
        # We can plot only runs 4,6,7 overlapped
        # monteCarloLoaded.executeCallbacks([4,6,7])
        # or execute the plot on all runs
        monteCarloLoaded.executeCallbacks()

        # Now we clean up data from this test
        shutil.rmtree(dirName)
        assert not os.path.exists(dirName), "No leftover data should exist after the test"

        # And possibly show the plots
        if show_plots:
            if useDatashader and DATASHADER_FOUND:
                print "Test concluded, showing plots now via datashader"
                datashaderLibrary.datashaderDriver(DATASHADER_FOUND)
            else:
                print "Test concluded, showing plots now via matplot..."
                plt.show()
                # close the plots being saved off to avoid over-writing old and new figures
                plt.close("all")

    #########################################################
    if case ==2:
        # Now run initial cocnditions
        icName = bskPath + "/tests/testScripts/Support/run_MC_IC"
        monteCarlo.setICDir(icName)
        monteCarlo.setICRunFlag(True)
        numberICs = 3
        monteCarlo.setExecutionCount(numberICs)


        # Rerunning the case shouldn't fail
        runsList = list(range(numberICs))
        failed = monteCarlo.runInitialConditions(runsList)
        assert len(failed) == 0, "Should run ICs successfully"

        # monteCarlo.executeCallbacks([4,6,7])
        runsList = list(range(numberICs))
        monteCarlo.executeCallbacks(runsList)

        # And possibly show the plots
        if show_plots:
            if useDatashader and DATASHADER_FOUND:
                print "Test conclused, showing plots now via datashader"
                datashaderLibrary.datashaderDriver(DATASHADER_FOUND)
            else:
                plt.show()
                # close the plots being savfed off to avoid over-writing old and new figures
                plt.close("all")

        # Now we clean up data from this test
        os.remove(icName + '/' + 'MonteCarlo.data' )
        for i in range(numberICs):
            os.remove(icName + '/' + 'run' + str(i) + '.data')
        assert not os.path.exists(icName + '/' + 'MonteCarlo.data'), "No leftover data should exist after the test"

## This function creates the simulation to be executed in parallel.
# It is copied directly from src/tests/scenarios.
def createScenarioAttitudeFeedbackRW():

    # Create simulation variable names
    simTaskName = "simTask"
    simProcessName = "simProcess"

    #  Create a sim module as an empty container
    scSim = SimulationBaseClass.SimBaseClass()
    scSim.TotalSim.terminateSimulation()

    #
    #  create the simulation process
    #
    dynProcess = scSim.CreateNewProcess(simProcessName)

    # create the dynamics task and specify the integration update time
    simulationTimeStep = macros.sec2nano(0.5)
    dynProcess.addTask(scSim.CreateNewTask(simTaskName, simulationTimeStep))

    #
    #   setup the simulation tasks/objects
    #

    # initialize spacecraftPlus object and set properties
    scObject = spacecraftPlus.SpacecraftPlus()
    scObject.ModelTag = "spacecraftBody"
    # define the simulation inertia
    I = [0.0511, 0., 0.,
         0., 0.1522, 0.,
         0., 0., 0.1179]
    scObject.hub.mHub = 10.0                 # kg - spacecraft mass
    scObject.hub.r_BcB_B = [[0.0], [0.0], [0.0]] # m - position vector of body-fixed point B relative to CM
    scObject.hub.IHubPntBc_B = unitTestSupport.np2EigenMatrix3d(I)
    scSim.hubref = scObject.hub

    # add spacecraftPlus object to the simulation process
    scSim.AddModelToTask(simTaskName, scObject, None, 1)


    # clear prior gravitational body and SPICE setup definitions
    gravFactory = simIncludeGravBody.gravBodyFactory()
    gravBodies = gravFactory.createBodies(['earth', 'sun', 'moon'])

    # setup Earth Gravity Body
    earth = gravBodies['earth']
    earth.isCentralBody = True  # ensure this is the central gravitational body
    mu = earth.mu
    simIncludeGravBody.loadGravFromFile(bskPath + '/supportData/LocalGravData/GGM03S.txt'
                                        , earth.spherHarm
                                        , 100)

    # attach gravity model to spaceCraftPlus
    scObject.gravField.gravBodies = spacecraftPlus.GravBodyVector(gravFactory.gravBodies.values())

    # setup simulation start data/time
    timeInitString = "2020 March 1 00:28:30.0"
    spiceTimeStringFormat = '%Y %B %d %H:%M:%S.%f'
    timeInit = datetime.strptime(timeInitString, spiceTimeStringFormat)
    # setup SPICE module
    gravFactory.createSpiceInterface(bskPath + '/supportData/EphemerisData/', timeInitString)
    gravFactory.spiceObject.zeroBase = 'Earth'

    # add SPICE interface to task list
    scSim.AddModelToTask(simTaskName, gravFactory.spiceObject, None, -1)
    # attach gravity model to spaceCraftPlus
    scObject.gravField.gravBodies = spacecraftPlus.GravBodyVector(gravFactory.gravBodies.values())

    #
    #   set initial Spacecraft States
    #
    # setup the orbit using classical orbit elements
    oe = orbitalMotion.ClassicElements()
    orbitRadius = 550.0
    oe.a = (6371.0 + orbitRadius) * 1000.0  # meters
    oe.e = 0.0001
    oe.i = 55.0 * macros.D2R
    oe.Omega = 0.0 * macros.D2R
    oe.omega = 0.0 * macros.D2R
    oe.f = 180.0 * macros.D2R
    rN, vN = orbitalMotion.elem2rv(mu, oe)
    scObject.hub.r_CN_NInit = unitTestSupport.np2EigenVectorXd(rN)  # m   - r_CN_N
    scObject.hub.v_CN_NInit = unitTestSupport.np2EigenVectorXd(vN)  # m/s - v_CN_N
    scObject.hub.sigma_BNInit = [[0.1], [0.2], [-0.3]]  # sigma_BN_B
    scObject.hub.omega_BN_BInit = [[0.005 * macros.D2R], [0.005 * macros.D2R],
                                   [0.005 * macros.D2R]]  # rad/s - omega_CN_B

    # add the simple Navigation sensor module.  This sets the SC attitude, rate, position
    # velocity navigation message
    sNavObject = simple_nav.SimpleNav()
    sNavObject.ModelTag = "SimpleNavigation"
    scSim.AddModelToTask(simTaskName, sNavObject)

    #
    # setup sensors
    #

    # Add IMU Sensor
    ImuSensor = imu_sensor.ImuSensor()
    ImuSensor.ModelTag = "imusensor"
    r_SB_B = np.array([0.0, 0.0, 0.0])  # Sensor position wrt body frame origin
    ImuSensor.sensorPos_B = np.array(r_SB_B)

    # IMU Parameters
    accelLSBIn = 0.0  # Not Used
    gyroLSBIn = 0.0001  # Discretization value (least significant bit)
    senRotBiasIn = 0.0  # Rotational sensor bias
    senRotMaxIn = 50.0  # Gyro saturation value
    gyroScale = [1., 1., 1.]  # Scale factor for each axis
    errorBoundsGryo = [0] * 3  # Bounds random walk
    gyroNoise = 0.000  # Noise

    ImuSensor.setLSBs(accelLSBIn, gyroLSBIn)
    ImuSensor.senRotBias = np.array([senRotBiasIn] * 3)
    ImuSensor.senRotMax = senRotMaxIn
    ImuSensor.gyroScale = np.array(gyroScale)
    ImuSensor.PMatrixGyro = np.eye(3) * gyroNoise
    ImuSensor.walkBoundsGyro = np.array(errorBoundsGryo)

    # add IMU to Simulation Process
    scSim.AddModelToTask(simTaskName, ImuSensor)

    # Add Mag Meter
    MagMeter = mag_meter.MagMeter()
    MagMeter.ModelTag = "MagMeter"
    MagMeterNoise = 0.000002
    MagMeterBias = 0.0
    ImuSensor.senRotBias = np.array([MagMeterBias] * 3)
    MagMeter.PMatrix = np.eye(3) * MagMeterNoise
    MagMeter.inclination = oe.i
    MagMeter.orbitRadius = oe.a / 1000  # 6371.0 + orbitRadius
    scSim.AddModelToTask(simTaskName, MagMeter)

    # setup Sun Position
    pyswice.furnsh_c(gravFactory.spiceObject.SPICEDataPath + 'de430.bsp')  # solar system bodies
    pyswice.furnsh_c(gravFactory.spiceObject.SPICEDataPath + 'naif0011.tls')  # leap second file
    pyswice.furnsh_c(gravFactory.spiceObject.SPICEDataPath + 'de-403-masses.tpc')  # solar system masses
    pyswice.furnsh_c(gravFactory.spiceObject.SPICEDataPath + 'pck00010.tpc')  # generic Planetary Constants Kernel
    sunPositionMsg = simMessages.SpicePlanetStateSimMsg()
    sunInitialState = 1000 * pyswice.spkRead('SUN', timeInitString, 'J2000', 'EARTH')
    rN_sun = sunInitialState[0:3]  # meters
    vN_sun = sunInitialState[3:6]  # m/s
    sunPositionMsg.PositionVector = rN_sun
    sunPositionMsg.VelocityVector = vN_sun


    #
    #   setup the FSW algorithm tasks
    #

    # setup inertial3D guidance module
    inertial3DConfig = inertial3D.inertial3DConfig()
    inertial3DWrap = scSim.setModelDataWrap(inertial3DConfig)
    inertial3DWrap.ModelTag = "inertial3D"
    scSim.AddModelToTask(simTaskName, inertial3DWrap, inertial3DConfig)
    inertial3DConfig.sigma_R0N = [0., 0., 0.]       # set the desired inertial orientation
    inertial3DConfig.outputDataName = inertial3DConfigOutputDataName

    # setup the attitude tracking error evaluation module
    attErrorConfig = attTrackingError.attTrackingErrorConfig()
    attErrorWrap = scSim.setModelDataWrap(attErrorConfig)
    attErrorWrap.ModelTag = "attErrorInertial3D"
    scSim.AddModelToTask(simTaskName, attErrorWrap, attErrorConfig)
    attErrorConfig.outputDataName = attErrorConfigOutputDataName
    attErrorConfig.inputRefName = inertial3DConfig.outputDataName
    attErrorConfig.inputNavName = sNavObject.outputAttName


    # setup the BDOT Feedback control module
    bdotControlConfig = B_DOT.B_DOTConfig()
    bdotControlWrap = scSim.setModelDataWrap(bdotControlConfig)
    bdotControlWrap.ModelTag = "B_DOT"
    scSim.AddModelToTask(simTaskName, bdotControlWrap, bdotControlConfig)
    bdotControlConfig.inputMagMeterName = MagMeter.outputStateMessage
    bdotControlConfig.vehConfigInMsgName = "vehicleConfigName"
    bdotControlConfig.outputDataName = "LrRequested"
    bdotControlConfig.K_detumble = 200000.0

    bdotControlConfig.use_rw_wheels = 0
    torqueRodConfig = torqueRodDynamicEffector.torqueRodDynamicEffector()
    # torqueRodWrap = scSim.setModelDataWrap(torqueRodConfig)
    torqueRodConfig.ModelTag = "torqueRods"
    torqueRodConfig.magFieldMsgName = MagMeter.outputStateMessage
    torqueRodConfig.cmdTorqueRodsMsgName = bdotControlConfig.outputDataName
    torqueRodConfig.MaxDipoleMoment = 0.11*100  # [Am^2]
    scObject.addDynamicEffector(torqueRodConfig)
    scSim.AddModelToTask(simTaskName, torqueRodConfig)

    #
    # create simulation messages
    #

    # create the FSW vehicle configuration message
    vehicleConfigOut = fswMessages.VehicleConfigFswMsg()
    vehicleConfigOut.ISCPntB_B = I  # use the same inertia in the FSW algorithm as in the simulation
    unitTestSupport.setMessage(scSim.TotalSim,
                               simProcessName,
                               bdotControlConfig.vehConfigInMsgName,
                               vehicleConfigOut)




    # This is a hack because of a bug in Basilisk... leave this line it keeps
    # variables from going out of scope after this function returns
    scSim.additionalReferences = [scObject, earth, bdotControlWrap, attErrorWrap, inertial3DWrap]

    return scSim

def executeScenario(sim):
    #
    #   initialize Simulation
    #
    sim.InitializeSimulationAndDiscover()

    #
    #   configure a simulation stop time time and execute the simulation run
    #
    sim.ConfigureStopTime(simulationTime)
    sim.ExecuteSimulation()

# This method is used to plot the retained data of a simulation.
# It is called once for each run of the simulation, overlapping the plots
def plotSim(data, retentionPolicy):
    #
    #   retrieve the logged data
    #



    dataSigmaBR = data["messages"][attErrorConfigOutputDataName+".sigma_BR"]
    dataOmegaBR = data["messages"][attErrorConfigOutputDataName+".omega_BR_B"]
    dataPos = data["messages"][sNavObjectOutputTransName+".r_BN_N"]
    dataOmegaBN = data["messages"][sNavObjectOutputAttName + ".omega_BN_B"]
    dataRW = []

    np.set_printoptions(precision=16)

    #
    #   plot the results
    #

    timeData = dataSigmaBR[:, 0] * macros.NANO2HOUR

    figureList = {}
    plt.figure(1)
    pltName = 'AngularRates'
    for idx in range(1, 4):
        plt.plot(timeData, dataOmegaBN[:, idx] * macros.R2D,
                 label='Run ' + str(data["index"]) + ' $\omega_{BN,' + str(idx) + '}$')
    # plt.legend(loc='lower right')
    plt.xlabel('Time [hour]', fontsize=34)
    plt.ylabel('Angular Rates (deg/s) ', fontsize=34)
    plt.title('Spacecraft Angular Rates', fontsize=34)
    plt.tick_params(labelsize=34)
    p1ds = plt.axhline(y=1, color='r', linestyle='--')
    n1ds = plt.axhline(y=-1, color='r', linestyle='--')
    plt.legend((p1ds, n1ds), ('+ 1 deg/s', '- 1 deg/s'), loc='upper right', fontsize=30)

    figureList[pltName] = plt.figure(1)



    return figureList

def plotSimAndSave(data, retentionPolicy):
    figureList = plotSim(data, retentionPolicy)
    for pltName, plt in figureList.items():
        # plt.subplots_adjust(top = 0.6, bottom = 0.4)
        unitTestSupport.saveScenarioFigure(
            fileNameString + "_" + pltName
            , plt, path)

    return


################################################################
# DATASHDER CODE

# Function user can customize to configure the datashader libreary
def configureDatashader():

    # begin datashade configuration

    if not DATASHADER_FOUND:
        return

    # Below are some optional settings you can configure. To set them, uncomment the
    # the declaration line, and uncomment the line in the datashaderLibrary.configure(...) method below.

    # Set directories that the datashading library will generate. First directory name in this list is where
    # the csv files are saved, the second is where images, and html files are saved.
    # By default these are: `/mc1_data/` and `/mc1_assets/`
    # datashaderDirectories = ["/mc1_data_files/", "/mc1_assets_images/"]

    # Set which graphing techniques the library uses. Options: 'holoviews_datashader', 'only_datashader', 'both'.
    # The holoviews_datashader option allows the graph to have dyanmically generated axis
    # values, whereas the datashaer option provides a higher resolution image, but without any axes information or labeling.
    # If you want to plot just with datashader instead of holoviews, configure this variable and pass it in
    # the configure() methods as 'graphingTechnique = datashaderGraphType'. By default it will use the
    # holoviews interface to graph.
    datashaderGraphType = "both"

    # Set the html filename. Default is "mc_graphs.html"
    # Would pass in as : `htmlName = fileName`
    # fileName = "monte_carlo_graphs.html"

    # List of tuples that consist of: (message index, corresponding y axis label, title, etc for that data).
    # When setting graphRange, you can use (0,0) to use the default min / max of the values for either x or y.
    # For example, setting `graphRanges = (0,8), (0,0)`, sets the x range from 0 to 8, and keeps the y range as
    # the default minimum and maximum values of the y range.
    # The default unit of time is in seconds using the macro NANO2SEC; however, this can be changed by
    # passing in a different macro from `macros.py` to multiply your x data range by that macro.
    # Note: The time unit must align with the x and y range you set. If the graph is set to minutes,
    # the range should be in minutes as well.
    # Every value except `dataIndex` has default values so they do not need to be set. In the datashadingLibrary
    # this index is used to parse into the messages dictionary to retrieve the data in the callback function.
    # Such as: dataMessage = data["messages"][index]
    # You can also customize the name of the directories that will be created while datashading:
    # datashaderDirectories = ["/mc1_data_files/", "/mc1_assets_images/"]
    # You can also customize the name of the html file that is generated and holds the graphs:
    # fileName = "monte_carlo_graphs.html"
    # You can pass these values into the configure method below to set them in the library.
    Graph = datashaderLibrary.DatashaderGraph
    datashaderDataList = [
        Graph(dataIndex=attErrorConfigOutputDataName + ".sigma_BR", yaxislabel="Attitude error (sigma)",
              title="Attitude Error History", xaxislabel="Time [minutes]", color="fire",
              graphRanges=[(0, 8), (0, 0)], dpi=400, macro=macros.NANO2MIN),
        Graph(dataIndex=attErrorConfigOutputDataName + ".omega_BR_B", yaxislabel="Rate Tracking Error (rad/s)",
              title="Attitude Tracking Error History", xaxislabel = "Time [seconds]", color = "fire",
              graphRanges=[(100, 600), (-0.02, 0.02)], dpi=500, macro = macros.NANO2SEC)]

    # Set whether or not the datashading library will save data to CSV files
    # This is set to false by default in the library
    datashaderLibrary.saveData = True

    # Configure the lbirary to use the list of graphs, and any other settings
    # that may have been set.
    datashaderLibrary.configure(dataConfiguration=datashaderDataList
                                # ,directories=datashaderDirectories
                                , graphingTechnique=datashaderGraphType
                                # ,fileName = "monte_carlo_graphs.html"
                                )

    if ONLY_GRAPH_DATA:
        print "Datashading from existing csv files"
        datashaderLibrary.graph(fromCSV = True)
        return

# END DATASHADER CODE
################################################################
#
# This statement below ensures that the unit test script can be run as a
# # stand-along python script
#
if __name__ == "__main__":
    run(  saveFigures=False        # save figures to file
        , case=1            # Case 1 is normal MC, case 2 is initial condition run
        , show_plots=True         # show_plots.
          # THIS MUST BE FALSE BY DEFAULT
        , useDatashader=False         # use datashading library - matplotlib will not be used
       )

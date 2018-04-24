import React from 'react';
import { BrowserRouter as Router, Route, Redirect } from 'react-router-dom';
import SpacyComponent from './components/SpacyComponent';

/*******************************************************************************
  <App /> Container
*******************************************************************************/

const DEFAULT_PATH = "/spacy-parser"

// The App is just a react-router wrapped around the Demo component.
const App = () => (
  <Router>
    <div>
      <Route exact path="/" render={() => (
        <Redirect to={DEFAULT_PATH}/>
      )}/>
      <Route path="/:model" component={Demo}/>
    </div>
  </Router>
)

class Demo extends React.Component {
  constructor(props) {
    super(props);

    // React router supplies us with a model name and (possibly) a slug.
    const { model } = props.match.params;

    this.state = {
      selectedModel: model,
      requestData: null,
      responseData: null
    };

    // We'll need to pass this to the Header component so that it can clear
    // out the data when you switch from one model to another.
    this.clearData = () => {
      this.setState({requestData: null, responseData: null})
    }

    // Our components will be using history.push to change the location,
    // and they will be attaching any `requestData` and `responseData` updates
    // to the location object. That means we need to listen for location changes
    // and update our state accordingly.
    props.history.listen((location, action) => {
      const { state } = location;
      if (state) {
        const { requestData, responseData } = state;
        this.setState({requestData, responseData})
      }
    });
  }

  // We also need to update the state whenever we receive new props from React router.
  componentWillReceiveProps({ match }) {
    const { model } = match.params;
    this.setState({selectedModel: model});
  }

  render() {
    const { requestData, responseData } = this.state;

    const ModelComponent = () => {
        return (<SpacyComponent requestData={requestData} responseData={responseData}/>)
    }

    return (
      <div className="pane-container">
        <ModelComponent />
      </div>
    );
  }
}

export default App;

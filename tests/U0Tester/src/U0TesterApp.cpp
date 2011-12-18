#include "cinder/app/AppBasic.h"
#include "cinder/gl/gl.h"

using namespace ci;
using namespace ci::app;
using namespace std;

class U0TesterAppApp : public AppBasic {
  public:
    void prepareSettings( Settings *settings );
	void setup();
	void mouseDown( MouseEvent event );	
    void keyDown( KeyEvent event );
    void keyUp( KeyEvent event );
	void update();
	void draw();

private:
    bool *states;
};


void U0TesterAppApp::prepareSettings( Settings *settings ) {
    settings->setWindowSize( 1920, 1080 );
    settings->setFrameRate( 60.0f );
    settings->setFullScreen( true );
}

void U0TesterAppApp::setup()
{
    states = new bool[5];

    for (int i=0 ; i<5 ; ++i) {
        states[i] = false;
    }
    hideCursor();
    hideCursor();
    hideCursor();
    hideCursor();
}

void U0TesterAppApp::mouseDown( MouseEvent event )
{
}

void U0TesterAppApp::update()
{
}

void U0TesterAppApp::keyDown( KeyEvent event )
{
    char ch = event.getChar();

    if (ch == 27) {
        quit();
    }

    if (ch < '1' || ch > '5') {
        return;
    } else {
        states[ch - '1'] = true;
    }
}

void U0TesterAppApp::keyUp( KeyEvent event )
{
    char ch = event.getChar(); 
    if (ch < '1' || ch > '5') {
        return;
    } else {
        states[ch - '1'] = false;
    }
}

void U0TesterAppApp::draw()
{
    gl::setMatricesWindow( getWindowSize() );
	// clear out the window with black
	gl::clear( Color( 0, 0, 0 ) );

    for (int i=0 ; i < 5 ; ++i) {
        int offset = 110 * i;

        if (states[i]) {
            glColor3f( 1.0f, 0.5f, 0.25f );
        } else {
            glColor3f( 0.2f, 0.2f, 0.2f );
        }

        glBegin( GL_QUADS );
        glVertex2f(10 + offset, 10);
        glVertex2f(100 + offset, 10);
        glVertex2f(100 + offset, 100);
        glVertex2f(10 + offset, 100);
        glEnd();
    }
}

CINDER_APP_BASIC( U0TesterAppApp, RendererGl )

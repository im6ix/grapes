use std::{io, time::Duration};

use crossterm::{
    event::{self, Event, KeyCode}, 
    execute, 
    terminal::{
        EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode
        }
};
use ratatui::{
    Frame, Terminal, 
    backend::CrosstermBackend, 
    style::Style,  
    widgets::{List, ListState, Paragraph}

};


const _GRAPES_ART: &str = "                                               
                 ⠀⠰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                 ⠀⠀⡂⠀
         ⠀⢠⢰⢐⠆⠀⠂⠂⠁⠅⠀
    ⠀⠀⠀⠀⠰⡢⡱⡱⠡⡀⡂⠀⠀⠅⠀⢀⢀⣀⡀⠀
      ⠀⠀⡩⡸⠨⡊⠔⡐⠈⠀⠠⢘⡊⠖⢵⡶⡮⣦⠀
        ⠀⢰⠑⠅⠂⢂⠤⢦⢆⢦⢅⢎⢬⡾⣷⣹⠗⠀⠀
        ⠀⢀⠠⠀⣇⢄⣷⠫⢟⠯⣦⢳⢽⡿⣽⢯⡷⣄⢖⡢⣄⠀
     ⠀⠐⠈⡀⢔⢴⣌⠧⡃⠡⡱⣕⢽⣜⢔⢕⢕⢿⡽⣘⣜⢮⡪⡃
      ⠀⢐⢈⢆⢯⢮⣿⣘⢼⢽⣾⣽⣿⣽⢽⡚⢍⣯⢞⢮⣷⠯⠃⠀⠀
     ⠀⠀⠀⠢⢳⡽⣯⣿⢕⢝⣯⣷⡿⣝⣞⣏⠣⡢⡿⣝⣵⠃⠀
         ⠀⠐⠽⠽⠿⠊⢜⢬⢹⡽⠪⢚⡾⡮⣯⣿⢿⣎⠀
         ⠀⠀⠀⢢⢡⣣⣳⣟⣧⢱⣸⣟⣮⢿⣯⣷⣳⠇⠀
           ⠠⡐⠡⡱⣹⠟⡚⣝⡳⣽⢽⣟⣟⡿⡛⠚⠃⠀
          ⠈ ⢎⢎⡾⡆⡅⢬⣖⣝⣾⡷⡵⡽⣮⣇⠀⠀
            ⠈⠉⠩⡋⡞⣵⣿⢷⢟⢝⡝⡿⣽⣺⠄
             ⠀⠨⣎⣮⣷⣿⠱⡱⣱⣝⣮⠛⠁
             ⠀⠀⢨⢂⢣⢷⡵⡟⠟⠃⠀
                ⠸⡦⣳⣿⣽⡃⠀     
                  ⠉⠛⠓⠁⠀

";

enum Screen {
    Splash,
    Provider,
    Config,
    OpenAI,
}


fn main() -> Result<(), io::Error> {
    enable_raw_mode()?; // captures key presses and stuff
    let mut stdout = io::stdout(); // writes output to the terminal

    execute!(stdout, EnterAlternateScreen)?; // to enter an alternate screen so we dont mess up out terminal
    let backend = CrosstermBackend::new(stdout); 
    let mut terminal = Terminal::new(backend)?; // terminal manages drawing frames and buffering updates
    let mut state = ListState::default();
    let mut screen = Screen::Splash;
    
    loop {
        terminal.draw(|frame| {

            match screen {
                Screen::Splash => draw_splash(frame),
                Screen::Provider => draw_provider(frame, &mut state),
                Screen::Config => draw_config(frame),
                Screen::OpenAI => open_ai(frame),
                
            }
            
        })?;

        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(k) = event::read()? {
                
                match screen {
                    Screen::Splash => {
                        if k.code == KeyCode::Enter {
                            screen = Screen::Provider;
                        }
                    }
                    Screen::Provider => {
                        if k.code == KeyCode::Down {
                            state.select_next();
                        }
                        if k.code == KeyCode::Up {
                            state.select_previous();
                        }
                        if k.code == KeyCode::Enter{
                              if let Some(index) = state.selected() {
                                match index {
                                    0 => screen = Screen::OpenAI,
                                    _ => {}
                                }
                            }
                                                    
                        }

                    }
                    Screen::Config => {
                        if k.code == KeyCode::Enter {
                            break;
                        }
                    }
                    Screen::OpenAI => {
                        if k.code == KeyCode::Enter {
                            screen = Screen::Config
                        }
                    }
                }



                if k.code == KeyCode::Esc {
                    break;
                }
            };
        }
    };



    disable_raw_mode()?; //restores normal terminal behaviour
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?; // raw mode hides the curosr so we need to show it again

    Ok(())

}


fn draw_splash(frame: &mut Frame){
    let user_info = Paragraph::new("usere info");
    frame.render_widget(user_info, frame.area());
}

fn draw_provider(frame: &mut Frame, state:&mut ListState) {
    let providers = ["OpenAI", "Anthropic", "Ollama"];
    let list = List::new(providers)
    .highlight_style(Style::new().italic())
    .highlight_symbol(">>");

    frame.render_stateful_widget(list, frame.area(), state);

}

fn draw_config(frame: &mut Frame) {
    let config = Paragraph::new("user_config");
    frame.render_widget(config, frame.area());
}

fn open_ai(frame: &mut Frame){
    let api_key = Paragraph::new("user's api key: 000666");
    frame.render_widget(api_key, frame.area());
}